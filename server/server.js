const { exec } = require('child_process');
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
const recordingsPath = './public/recordings'

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
        console.log(`Client disconnected: ${clientId}`);
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

function convertToMp4(inputPath, outputPath) {
    return new Promise((resolve, reject) => {
        const command = `ffmpeg -i "${inputPath}" -c:v libx264 -preset ultrafast -crf 22 -c:a aac -b:a 128k "${outputPath}"`;

        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error: ${error}`);
                return reject(error);
            }

            // Delete the original file after successful conversion
            fs.unlink(inputPath, (err) => {
                if (err) {
                    console.error(`Error deleting original file ${inputPath}: ${err}`);
                    return reject(err);
                }
                console.log(`Deleted original file: ${inputPath}`);
                resolve(outputPath);
            });
        });
    });
}



function convertAllH264ToMp4(directory) {
    fs.readdir(directory, (err, files) => {
        if (err) {
            console.error('Error reading video files:', err);
            return;
        }

        files.forEach(file => {
            if (file.endsWith('.h264')) {
                const inputPath = `${directory}/${file}`;
                const outputPath = `${directory}/${file.replace('.h264', '.mp4')}`;

                // Check if the MP4 file already exists
                if (!fs.existsSync(outputPath)) {
                    console.log(`Converting ${file} to MP4...`);
                    convertToMp4(inputPath, outputPath)
                        .then(() => console.log(`${file} converted to MP4`))
                        .catch(error => console.error(`Failed to convert ${file}:`, error));
                }
            }
        });
    });
}

convertAllH264ToMp4('./public/recordings');

// endpoint to get list of video files on server
app.get('/video-list', (req, res) => {
    convertAllH264ToMp4(recordingsPath);
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
