document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.answer-btn');
    const resultModalElement = document.getElementById('resultModal');
    const resultModal = new bootstrap.Modal(resultModalElement);
    const resultText = document.getElementById('resultText');
    const resultIcon = document.getElementById('resultIcon');
    const newWordBadge = document.getElementById('newWordBadge');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const answerId = this.getAttribute('data-id');
            const checkUrl = this.getAttribute('data-check-url');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(checkUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    'answer_id': answerId
                })
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                if (data.is_new) {
                    newWordBadge.classList.remove('d-none');
                } else {
                    newWordBadge.classList.add('d-none');
                }
                resultText.innerText = data.message;
                resultText.className = "mb-4 fw-bold";
                if(data.text_class) {
                    resultText.classList.add(data.text_class);
                }
                if(data.icon) {
                    resultIcon.innerText = data.icon;
                }

                resultModal.show();
            })
            .catch(error => {
                console.error('Error:', error);
                alert("Wystąpił błąd połączenia z serwerem.");
            });
        });
    });
});