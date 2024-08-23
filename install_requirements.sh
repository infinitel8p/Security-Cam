#!/bin/bash

# Pull the latest code from the repository
git config --global --add safe.directory /opt/security-cam
cd /opt/security-cam/ || { echo "Failed to change directory to /opt/security-cam/"; exit 1; }
git pull || { echo "git pull failed"; exit 1; }

# Ensure the install_requirements.sh script is executable
# chmod +x /opt/security-cam/install_requirements.sh

# Install system packages and Python dependencies 
# cd /opt/security-cam/client || { echo "Failed to change directory to /opt/security-cam/client"; exit 1; }
# bash /opt/security-cam/install_requirements.sh || { echo "install_requirements.sh failed"; exit 1; }

# Install Node.js dependencies for the server
cd /opt/security-cam/server || { echo "Failed to change directory to /opt/security-cam/server"; exit 1; }
npm install || { echo "npm install failed"; exit 1; }

# Install the Bluetooth development headers required for pybluez
if dpkg -s libbluetooth-dev >/dev/null 2>&1; then
    echo "libbluetooth-dev is already installed, skipping..."
else
    sudo apt-get update || { echo "apt-get update failed"; exit 1; }
    sudo apt-get install -y libbluetooth-dev || { echo "Failed to install libbluetooth-dev"; exit 1; }
fi

# Install expect for automated Bluetooth pairing
if dpkg -s expect >/dev/null 2>&1; then
    echo "expect is already installed, skipping..."
else
    sudo apt-get install -y expect || { echo "Failed to install expect"; exit 1; }
fi

# Path to the requirements.txt file
REQUIREMENTS_FILE="/opt/security-cam/requirements.txt"

# Loop through each line in requirements.txt
while IFS= read -r package
do
    # Extract the package name before any version specifier (e.g., flask==2.0 -> flask)
    package_name=$(echo "$package" | cut -d '=' -f 1)
    
    # Install the package using apt-get if available, otherwise fallback to pip
    if apt-cache search --names-only "^python3-$package_name$" | grep -q "^python3-$package_name"; then
        sudo apt-get install -y python3-$package_name
    else
        sudo pip3 install "$package" --break-system-packages
    fi
done < "$REQUIREMENTS_FILE"
