document.addEventListener('DOMContentLoaded', function () {
    // Highlight the active tab based on the current URL
    const currentUrl = window.location.href;
    const baseUrl = window.location.origin + '/';
    const navbarItems = document.querySelectorAll('.navbar li');

    navbarItems.forEach(item => {
        const link = item.querySelector('a');

        if (link.href === currentUrl || (link.href === baseUrl + 'index.html' && currentUrl === baseUrl + 'index.html')) {
            item.classList.add('active-tab');
        }
    });
});
