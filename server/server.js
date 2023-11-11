const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const app = express();
const port = 3000;

// Serve static files from the 'public' directory
app.use(express.static('public'));

// Create an HTTP server
const server = http.createServer(app);

// Create a WebSocket server
const wss = new WebSocket.Server({ server });

let connectedClients = 0;

wss.on('connection', function connection(ws) {
    connectedClients++;
    console.log('A new client connected! Total clients:', connectedClients);

    ws.on('message', function incoming(data) {
        if (connectedClients > 1) {
            // Broadcast the received data (video frame) to all connected clients
            wss.clients.forEach(function each(client) {
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    client.send(data);
                }
            });
        }
    });

    ws.on('close', () => {
        connectedClients--;
        console.log('Client disconnected. Total clients:', connectedClients);
    });
});

// Start the server
server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});
