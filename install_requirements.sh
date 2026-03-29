#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Installing Node.js 22 (via NodeSource) ==="
NODE_MAJOR=$(node --version 2>/dev/null | sed 's/v\([0-9]*\).*/\1/')
if [ -z "$NODE_MAJOR" ] || [ "$NODE_MAJOR" -lt 22 ]; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
else
    echo "Node.js $NODE_MAJOR already installed, skipping."
fi

echo "=== Installing system packages ==="
sudo apt-get update
sudo apt-get install -y $(grep -v '^\s*#' "$SCRIPT_DIR/required-apt-packages.txt" | grep -v '^\s*$')

echo "=== Setting up Python virtual environment ==="
python3 -m venv venv --system-site-packages
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r "$SCRIPT_DIR/requirements.txt"

echo "=== Installing Node.js dependencies ==="
cd "$SCRIPT_DIR/server"
npm install

echo "=== Building frontend ==="
npm run build

echo "=== Done ==="
