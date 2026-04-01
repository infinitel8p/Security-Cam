#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# --- Set up logging ---
LOG_DIR="$SCRIPT_DIR/logs/install"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date '+%Y-%m-%d_%H-%M-%S').log"
exec > >(tee -a "$LOG_FILE") 2>&1
ls -1t "$LOG_DIR"/*.log 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null || true

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
sudo -u pi npm install

# Build to a temp directory so a failed build doesn't destroy the previous one
sudo -u pi npx astro build --outDir dist_new
rm -rf dist
mv dist_new dist

echo "=== Done ==="
