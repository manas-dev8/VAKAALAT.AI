function searchLawyers() {
    const searchInput = document.getElementById('searchInput').value;
    fetch(`/search_lawyers?query=${searchInput}`)
        .then(response => response.json())
        .then(data => {
            displayLawyerCards(data.lawyers);
        });
}

function displayLawyerCards(lawyers) {
    const lawyerCardsContainer = document.getElementById('lawyerCards');
    lawyerCardsContainer.innerHTML = '';

    lawyers.forEach(lawyer => {
        const card = document.createElement('div');
        card.classList.add('lawyer-card');

        const image = document.createElement('img');
        image.src = lawyer.image_path;
        card.appendChild(image);

        const content = document.createElement('div');
        content.classList.add('lawyer-card-content');

        const name = document.createElement('h2');
        name.textContent = lawyer.name;
        content.appendChild(name);

        const description = document.createElement('p');
        description.textContent = lawyer.description;
        content.appendChild(description);

        card.appendChild(content);
        lawyerCardsContainer.appendChild(card);
    });
}

document.addEventListener('DOMContentLoaded', function () {
    var joinBtn = document.getElementById('joinBtn');
    var popupForm = document.getElementById('popupForm');
    var closeButton = document.getElementsByClassName('close')[0];

    joinBtn.addEventListener('click', function () {
        popupForm.style.display = 'block';
    });

    closeButton.addEventListener('click', function () {
        popupForm.style.display = 'none';
    });

    
    window.onclick = function (event) {
        if (event.target == popupForm) {
            popupForm.style.display = 'none';
        }
    };
});
