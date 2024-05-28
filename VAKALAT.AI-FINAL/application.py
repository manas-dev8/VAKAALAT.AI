##   IMPORTING LIBRARIES AND DEPENDANCIES
from flask import Flask, render_template, request, redirect, url_for,session
import os
from src.utils import download_hugging_face_embeddings
from langchain.prompts import PromptTemplate
from langchain.llms import CTransformers
from langchain.chains import RetrievalQA
from src.prompt import *
from langchain.vectorstores import FAISS
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from werkzeug.utils import secure_filename
from langchain.llms import Replicate
import csv

##    Initializing Flask app
app = Flask(__name__)
os.environ['REPLICATE_API_TOKEN'] = "r8_4wcTjFXcdJuYoDMD5EvJX9z83c1wJDv0jPLb7"

CSV_FILE = 'lawyers.csv'
if os.path.exists(CSV_FILE):
    lawyers_df = pd.read_csv(CSV_FILE)
else:
    lawyers_df = pd.DataFrame(columns=['id', 'name', 'description', 'image_path'])

def recommend_lawyers(query):
    global lawyers_df

    if query:
        # Filter lawyers based on search query
        filtered_lawyers = lawyers_df[lawyers_df['description'].str.contains(query, case=False)]
        # Convert filtered lawyers to dictionary format
        lawyer_data = filtered_lawyers.to_dict(orient='records')
    else:
        # Randomly select 3 lawyers if no search query is provided
        random_lawyers = lawyers_df
        # Convert randomly selected lawyers to dictionary format
        lawyer_data = random_lawyers.to_dict(orient='records')

    return lawyer_data

## DATABASE
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.email
##   LLM INITIALIZATION
embeddings = download_hugging_face_embeddings()

vdb = FAISS.load_local("vector_stores/faiss_index", embeddings)

PROMPT=PromptTemplate(template=prompt_template, input_variables=["context", "question"])

chain_type_kwargs={"prompt": PROMPT}

llm=CTransformers(model="model\llama-2-7b-chat.ggmlv3.q4_0.bin",
                  model_type="llama",
                  config={'max_new_tokens':512,
                          'temperature':0.08})
# Initialize Replicate Llama2 Model
# llm = Replicate(
#     model="a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5",
#     input={"temperature": 0.75, "max_length": 3000}
# )
qa=RetrievalQA.from_chain_type(
    llm=llm, 
    chain_type="stuff", 
    retriever=vdb.as_retriever(search_kwargs={'k': 3}),
    return_source_documents=True, 
    chain_type_kwargs=chain_type_kwargs
    )

##     HOME PAGE
@app.route('/')
def home():
    return render_template('home.html')

## LOGIN/ SIGNUP
@app.route('/signup')
def signup_page():
    signup_success = session.pop('signup_success', False)
    return render_template('signup.html', signup_success=signup_success)

@app.route('/signup', methods=['POST'])
def signup():
    full_name = request.form['full_name']
    email = request.form['email']
    password = request.form['password']

    with app.app_context():
        # Check if the user already exists
        if User.query.filter_by(email=email).first() is not None:
            return "Email already exists. Please use a different email address."

        # Create a new user
        new_user = User(full_name=full_name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['signup_success'] = True
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    with app.app_context():
        # Check if user exists and password matches
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['email'] = email
            return redirect('/')  # Redirect to options page upon successful login
        else:
            # Render index.html with error message
            return render_template('signup.html', login_error=True)

@app.route('/buy_documents')
def buy_documents():
    return render_template('buy_documents.html')

## LAWGPT
@app.route("/lawgpt")
def index():
    return render_template('chat.html')

@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    input = msg
    print(input)
    result=qa({"query": input})
    print("Response : ", result["result"])
    return str(result["result"])

@app.route('/lawyers')
def lawyers():
    query = request.args.get('query')
    recommended_lawyers = recommend_lawyers(query)
    return render_template('legal_connect.html', lawyers=recommended_lawyers)

@app.route('/join', methods=['POST'])
def join_as_lawyer():
    global lawyers_df

    # Get form data
    name = request.form['name']
    description = request.form['description']
    photo = request.files['photo']

    # Save photo to static/images folder
    photo_path = os.path.join('static', 'images', photo.filename)
    photo.save(photo_path)

    # Generate unique ID
    id = len(lawyers_df) + 1

    # Create a new DataFrame with the new row
    new_row = pd.DataFrame({'id': [id], 'name': [name], 'description': [description], 'image_path': [photo_path]})

    # Concatenate the new DataFrame with the existing DataFrame
    lawyers_df = pd.concat([lawyers_df, new_row], ignore_index=True)

    # Save DataFrame to CSV
    lawyers_df.to_csv(CSV_FILE, index=False)

    return redirect(url_for('success'))

@app.route('/success')
def success():
    return render_template('success.html')

# RUN The WEBSITE
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
