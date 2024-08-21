#!/bin/bash

# Start the Node.js server
cd /opt/security-cam/server || exit
npm run dev &

# Start the Flask server
cd /opt/security-cam/client || exit
python3 main.py &
