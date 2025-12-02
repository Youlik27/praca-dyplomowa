document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('addWordInput');
    const resultsDiv = document.getElementById('addWordResults');
    const form = document.getElementById('addWordForm');

    if (!input || !resultsDiv) return;

    let debounceTimer;

    input.addEventListener('input', function() {
        const query = this.value.trim();

        clearTimeout(debounceTimer);

        if (query.length < 2) {
            hideResults();
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/search/?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    showResults(data);
                })
                .catch(err => {
                    console.error('Błąd wyszukiwania:', err);
                    hideResults();
                });
        }, 300);
    });

    function showResults(data) {
        resultsDiv.innerHTML = '';

        if (data.length === 0) {
            hideResults();
            return;
        }

        resultsDiv.classList.add('dropdown-menu', 'show', 'w-100', 'shadow-lg', 'border-0');

        data.forEach(item => {
            const resultItem = document.createElement('button');
            resultItem.type = 'button';
            resultItem.classList.add('dropdown-item', 'd-flex', 'justify-content-between', 'align-items-center', 'py-2');

            resultItem.innerHTML = `
                <div>
                    <span class="fw-bold">${escapeHTML(item.word)}</span>
                    <small class="text-muted d-block text-truncate" style="max-width: 250px;">
                        ${escapeHTML(item.description || item.translation || '')}
                    </small>
                </div>
                <i class='bx bx-plus-circle text-primary fs-4'></i>
            `;

            resultItem.addEventListener('click', (e) => {
                e.preventDefault();
                selectWord(item.word);
            });

            resultsDiv.appendChild(resultItem);
        });
    }

    function selectWord(word) {
        input.value = word;
        hideResults();
        form.submit();
    }

    function hideResults() {
        resultsDiv.innerHTML = '';
        resultsDiv.classList.remove('dropdown-menu', 'show', 'w-100', 'shadow-lg');
    }

    document.addEventListener('click', function(event) {
        if (!input.contains(event.target) && !resultsDiv.contains(event.target)) {
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