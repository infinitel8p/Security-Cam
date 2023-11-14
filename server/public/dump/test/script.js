document.addEventListener("DOMContentLoaded", function () {
    barba.init({
        views: [{
            namespace: 'home',
            beforeEnter() {
                document.getElementById('home-btn').classList.add('active');
                document.getElementById('recordings-btn').classList.remove('active');
            }
        }, {
            namespace: 'recordings',
            beforeEnter({ next }) {
                fetch('./recordings.html')
                    .then(response => response.text())
                    .then(html => {
                        next.container.innerHTML = html;
                        console.log(html)
                    });
                document.getElementById('home-btn').classList.remove('active');
                document.getElementById('recordings-btn').classList.add('active');
            }
        }],
        transitions: [{
            leave({ current }) {
                // Animation or transition for leaving page
            },
            enter({ next }) {
                // Animation or transition for entering page
            }
        }]
    });
});
