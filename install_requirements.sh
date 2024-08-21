#!/bin/bash

# Update package list
sudo apt-get update

# Install system dependencies
sudo apt-get install -y python3 python3-pip nodejs npm

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
