document.addEventListener("DOMContentLoaded", function() {
        var activeTab = localStorage.getItem('activeTab');
        if (activeTab) {
            var tabElement = document.querySelector('button[data-bs-target="' + activeTab + '"]');
            if(tabElement) {
                var tab = new bootstrap.Tab(tabElement);
                tab.show();
            }
        }
        var tabButtons = document.querySelectorAll('button[data-bs-toggle="tab"]');
        tabButtons.forEach(function(btn) {
            btn.addEventListener('shown.bs.tab', function (e) {
                var targetId = e.target.getAttribute('data-bs-target');
                localStorage.setItem('activeTab', targetId);
            });
        });
    });