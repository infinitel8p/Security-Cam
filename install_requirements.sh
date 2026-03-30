#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# --- Node.js 22 via NodeSource ---
echo "=== Checking Node.js ==="
NODE_MAJOR=$(node --version 2>/dev/null | sed 's/v\([0-9]*\).*/\1/')
if [ -z "$NODE_MAJOR" ] || [ "$NODE_MAJOR" -lt 22 ]; then
    echo "Installing Node.js 22 via NodeSource..."
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
    sudo apt-get install -y nodejs
else
    echo "Node.js $(node --version) already installed."
fi

# --- System packages ---
echo "=== Installing system packages ==="
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $(grep -v '^\s*#' "$SCRIPT_DIR/required-apt-packages.txt" | grep -v '^\s*$')

# --- Python virtual environment ---
echo "=== Setting up Python virtual environment ==="
python3 -m venv venv --system-site-packages
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r "$SCRIPT_DIR/requirements.txt"

# --- Frontend ---
echo "=== Installing Node.js dependencies and building ==="
cd "$SCRIPT_DIR/server"
npm install
npm run build

echo "=== Done ==="
