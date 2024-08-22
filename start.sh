#!/bin/bash

# Pull the latest code from the repository
git pull || { echo "git pull failed"; exit 1; }

# Ensure the install_requirements.sh script is executable
chmod +x /opt/security-cam/install_requirements.sh

# Install system packages and Python dependencies 
cd /opt/security-cam/client || { echo "Failed to change directory to /opt/security-cam/client"; exit 1; }
bash /opt/security-cam/install_requirements.sh || { echo "install_requirements.sh failed"; exit 1; }

# Install Node.js dependencies for the server
cd /opt/security-cam/server || { echo "Failed to change directory to /opt/security-cam/server"; exit 1; }
npm install || { echo "npm install failed"; exit 1; }

# Start the Node.js server
cd /opt/security-cam/server || { echo "Failed to change directory to /opt/security-cam/server"; exit 1; }
npm start &

# Start the Flask server
cd /opt/security-cam/client || { echo "Failed to change directory to /opt/security-cam/client"; exit 1; }
python3 main.py &
