const canvas = document.getElementById('videoCanvas');
const context = canvas.getContext('2d');

const ws = new WebSocket('ws://localhost:3000');
ws.binaryType = 'blob';

let python_connected = false;

ws.onopen = function () {
    const clientInfo = {
        type: 'Browser',
        userAgent: navigator.userAgent
    };
    ws.send(JSON.stringify(clientInfo));
    showMessageOnCanvas("Searching for stream...");
};

ws.onmessage = function (event) {
    if (event.data === 'PYTHON_CONNECTED') {
        console.log('Python script connected');
        python_connected = true;
    } else if (event.data === 'PYTHON_DISCONNECTED') {
        console.log('Python script disconnected');
        python_connected = false;
        setTimeout(() => showMessageOnCanvas("Stream disconnected. Waiting for stream..."), 2000);
    } else if (python_connected) {
        const blob = new Blob([event.data], { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);
        const image = new Image();
        image.onload = function () {
            context.drawImage(this, 0, 0, canvas.width, canvas.height);
            URL.revokeObjectURL(url);
        };
        image.src = url;
    }
};

ws.onclose = function () {
    console.log('WebSocket connection closed');
}

function showMessageOnCanvas(message) {
    context.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
    context.font = '40px Arial'; // Set font size and style
    context.fillStyle = 'black'; // Set font color
    context.textAlign = 'center'; // Align text to center
    context.fillText(message, canvas.width / 2, canvas.height / 2); // Draw text on canvas
}
