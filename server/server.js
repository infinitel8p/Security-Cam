const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');
const app = express();
const port = 3000;

app.use(express.static('public'));
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

let clients = {};

// Handle WebSocket connection
wss.on('connection', function connection(ws) {
    let clientId;

    ws.on('message', function incoming(data) {
        if (!clientId) {
            clientId = data.toString();
            clients[clientId] = ws;
            updateClients();
            console.log(`Client connected: ${clientId}`);
            return;
        }

        // Regular message handling
        broadcastData(data, ws);
    });

    ws.on('close', () => {
        delete clients[clientId];
        updateClients();
    });
});

// Notify all clients about Python script connection status
function updateClients() {
    const isPythonConnected = !!clients['Python Script'];
    const isBrowserConnected = Object.keys(clients).some(id => id !== 'Python Script');

    if (clients['Python Script']) {
        // Tell the Python script to start/stop sending frames based on browser connection
        const message = isBrowserConnected ? 'START' : 'STOP';
        clients['Python Script'].send(message);
    }

    // Notify all browsers about Python script connection status
    Object.keys(clients).forEach(clientId => {
        if (clientId !== 'Python Script') {
            const message = isPythonConnected ? 'PYTHON_CONNECTED' : 'PYTHON_DISCONNECTED';
            clients[clientId].send(message);
        }
    });
}

// Broadcast data to all clients except sender
function broadcastData(data, senderWs) {
    Object.values(clients).forEach(client => {
        if (client !== senderWs && client.readyState === WebSocket.OPEN) {
            client.send(data);
        }
    });
}

// endpoint to get list of video files on server
app.get('/video-list', (req, res) => {
    const recordingsPath = './public/recordings'
    fs.readdir(recordingsPath, (err, files) => {
        if (err) {
            res.status(500).send('Error reading video files');
            return;
        }
        res.json(files.filter(file => file.endsWith('.mp4') || file.endsWith('.h264')));
    });
});

// start server
server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});
