document.addEventListener('DOMContentLoaded', () => {
    fetch('/video-list')
        .then(response => response.json())
        .then(videos => {
            const container = document.querySelector('.video-grid');
            videos.forEach(video => {
                const videoElement = document.createElement('video');
                videoElement.width = 320; // set your dimensions
                videoElement.height = 240;
                videoElement.controls = true;

                const sourceElement = document.createElement('source');
                sourceElement.src = `recordings/${video}`;
                sourceElement.type = 'video/mp4';

                videoElement.appendChild(sourceElement);
                container.appendChild(videoElement);
            });
        })
        .catch(error => console.error('Error fetching video list:', error));
});
