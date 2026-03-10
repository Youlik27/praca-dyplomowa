document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const resultsDiv = document.getElementById('resultsList');
    const searchForm = document.getElementById('searchForm');
    if (!searchInput) return;
    searchInput.addEventListener('input', function () {
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
    if (searchForm) {
        searchForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const query = searchInput.value.trim();
            if (query.length === 0) return;
            fetch(`/search/?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.length === 0) {
                        resultsDiv.innerHTML = `
                            <div class="p-3 text-center">
                                <span class="text-danger fw-bold">Nie znaleziono słowa: "${escapeHTML(query)}"</span>
                                <br>
                                <small class="text-muted">Sprawdź poprawność wpisanego tekstu.</small>
                            </div>
                        `;
                        resultsDiv.classList.add('dropdown-menu', 'show', 'w-100', 'shadow-lg');
                    } else {
                        const exactMatch = data.find(item => item.word.toLowerCase() === query.toLowerCase());

                        if (exactMatch) {
                            window.location.href = `/words/details/${encodeURIComponent(exactMatch.word)}`;
                        } else {
                            window.location.href = `/words/details/${encodeURIComponent(data[0].word)}`;
                        }
                    }
                })
                .catch(err => console.error('Błąd przy sprawdzaniu słowa:', err));
        });
    }

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
            itemLink.href = `/words/details/${encodeURIComponent(word.word)}`;
            itemLink.id = word.id;
            itemLink.innerHTML = `
                <div class="fw-bold text-dark">${escapeHTML(word.word)}</div>
            `;

            resultsDiv.appendChild(itemLink);
        });
    }

    function hideResults() {
        resultsDiv.innerHTML = '';
        resultsDiv.classList.remove('dropdown-menu', 'show', 'w-100', 'shadow-lg');
    }

    document.addEventListener('click', function (event) {
        if (!searchInput.contains(event.target) && !resultsDiv.contains(event.target)) {
            hideResults();
        }
    });

    function escapeHTML(str) {
        return (str ?? '').replace(/[&<>"']/g, function (match) {
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