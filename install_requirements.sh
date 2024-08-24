#!/bin/bash

# Pull the latest code from the repository
git config --global --add safe.directory /opt/security-cam
cd /opt/security-cam/ || { echo "Failed to change directory to /opt/security-cam/"; exit 1; }
git pull || { echo "git pull failed"; exit 1; }

# Install Node.js dependencies for the server
cd /opt/security-cam/server || { echo "Failed to change directory to /opt/security-cam/server"; exit 1; }
npm install || { echo "npm install failed"; exit 1; }

# Function to install a package if not already installed
install_if_needed() {
    if dpkg -s "$1" >/dev/null 2>&1; then
        echo "$1 is already installed, skipping..."
    else
        sudo apt-get install -y "$1" || { echo "Failed to install $1"; exit 1; }
    fi
}

# Ensure package list is up-to-date
sudo apt-get update || { echo "apt-get update failed"; exit 1; }

# Install the required packages
install_if_needed libbluetooth-dev
install_if_needed expect
install_if_needed nodejs
install_if_needed npm
install_if_needed python3
install_if_needed python3-pip
install_if_needed python3-smbus
install_if_needed i2c-tools
install_if_needed dnsmasq
install_if_needed hostapd
install_if_needed nftables

# Path to the requirements.txt file
REQUIREMENTS_FILE="/opt/security-cam/requirements.txt"

# Loop through each line in requirements.txt
while IFS= read -r package
do
    # Extract the package name before any version specifier (e.g., flask==2.0 -> flask)
    package_name=$(echo "$package" | cut -d '=' -f 1)
    
    # Install the package using apt-get if available, otherwise fallback to pip
    if apt-cache search --names-only "^python3-$package_name$" | grep -q "^python3-$package_name"; then
        sudo apt-get install -y python3-$package_name || { echo "Failed to install python3-$package_name"; exit 1; }
    else
        sudo pip3 install "$package" --break-system-packages || { echo "Failed to install $package using pip3"; exit 1; }
    fi
done < "$REQUIREMENTS_FILE"
