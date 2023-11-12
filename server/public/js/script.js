document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        const navLink = item.querySelector('.nav-link');
        let currentHref = window.location.href;

        if (currentHref.endsWith('/')) {
            currentHref += 'index.html';
        }

        if (navLink.href === currentHref) {
            navLink.classList.add('active');
        }
    });
});