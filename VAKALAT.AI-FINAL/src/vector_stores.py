from src.utils import text_split,load_pdf,download_hugging_face_embeddings
from langchain.vectorstores import FAISS

extracted_data = load_pdf("data/")
text_chunks = text_split(extracted_data)
embeddings = download_hugging_face_embeddings()

db = FAISS.from_documents(text_chunks, embeddings)
db.save_local("vector_stores/faiss_index")