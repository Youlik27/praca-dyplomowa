document.addEventListener('DOMContentLoaded', () => {

    const searchInput = document.getElementById('searchInput');
    const resultsDiv = document.getElementById('resultsList');

    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();

        if (query.length < 2) {
            hideResults();
            return;
        }

        fetch(`/search/?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                showResults(data);
            })
            .catch(err => {
                console.error('Błąd wyszukiwania:', err);
                hideResults();
            });
    });

    function showResults(data) {
        resultsDiv.innerHTML = '';
        resultsDiv.classList.add('dropdown-menu', 'show', 'w-100', 'shadow-lg');
        if (data.length === 0) {
            resultsDiv.innerHTML = '<span class="dropdown-item-text text-muted">Brak wyników.</span>';
            return;
        }

        data.forEach(word => {
            const itemLink = document.createElement('a');

            itemLink.classList.add('dropdown-item');
            itemLink.href = `/words/details/${word.word}`;
            itemLink.id = word.id;

            itemLink.innerHTML = `
                <div class="fw-bold text-dark">${escapeHTML(word.word)}</div>
                <small class="text-muted d-block text-truncate">
                    ${escapeHTML(word.description ?? '')}
                </small>
            `;

            resultsDiv.appendChild(itemLink);
        });
    }

    function hideResults() {
        resultsDiv.innerHTML = '';
        resultsDiv.classList.remove('dropdown-menu', 'show', 'w-100', 'shadow-lg');
    }
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target) && !resultsDiv.contains(event.target)) {
            hideResults();
        }
    });

    function escapeHTML(str) {
        return (str ?? '').replace(/[&<>"']/g, function(match) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[match];
        });
    }

});