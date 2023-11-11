const canvas = document.getElementById('videoCanvas');
const context = canvas.getContext('2d');

const ws = new WebSocket('ws://localhost:3000');
ws.binaryType = 'blob';

ws.onmessage = function (event) {
    const blob = new Blob([event.data], { type: 'image/jpeg' });

    const url = URL.createObjectURL(blob);

    const image = new Image();
    image.onload = function () {
        context.drawImage(this, 0, 0, canvas.width, canvas.height);
        URL.revokeObjectURL(url);
    };
    image.src = url;
};
