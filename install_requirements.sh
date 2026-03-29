#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

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

echo "=== Done ==="
