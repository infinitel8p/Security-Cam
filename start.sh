#!/bin/bash

# Start the Flask server
cd /opt/security-cam/client || { echo "Failed to change directory to /opt/security-cam/client"; exit 1; }
sudo python3 main.py &

# Start the Node.js server
cd /opt/security-cam/server || { echo "Failed to change directory to /opt/security-cam/server"; exit 1; }
npm start &

