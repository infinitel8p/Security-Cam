document.addEventListener('DOMContentLoaded', () => {
    fetch('/video-list')
        .then(response => response.json())
        .then(videos => {
            const container = document.querySelector('.video-grid');
            videos.forEach(video => {
                const videoElement = document.createElement('video');
                videoElement.width = 320;
                videoElement.height = 240;
                videoElement.controls = true;

                const sourceElement = document.createElement('source');
                sourceElement.src = `recordings/${video}`;

                // Determine the MIME type based on file extension
                const fileType = video.split('.').pop();
                if (fileType === 'mp4') {
                    sourceElement.type = 'video/mp4';
                } else if (fileType === 'h264') {
                    sourceElement.type = 'video/h264';
                }

                videoElement.appendChild(sourceElement);
                container.appendChild(videoElement);
            });
        })
        .catch(error => console.error('Error fetching video list:', error));
});
