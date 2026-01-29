function showEditForm() {
    const container = document.getElementById('display-name-container');
    const form = document.getElementById('edit-name-form');

    container.classList.add('d-none');
    form.classList.remove('d-none');

    const input = document.getElementById('list-name-input');
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
}

function hideEditForm() {
    document.getElementById('display-name-container').classList.remove('d-none');
    document.getElementById('edit-name-form').classList.add('d-none');
}

document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") {
        hideEditForm();
    }
});