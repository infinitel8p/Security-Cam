#!/bin/bash

PROJECT_DIR="/opt/security-cam"

# Start the Flask API server
cd "$PROJECT_DIR/client" || { echo "Failed to cd to client/"; exit 1; }
sudo python3 main.py &

# Serve the Astro frontend (static files, port 3000)
# Run 'npm run build' in server/ after any code changes or first install
cd "$PROJECT_DIR/server" || { echo "Failed to cd to server/"; exit 1; }
npm start &
