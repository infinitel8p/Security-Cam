#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Installing system packages ==="
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-opencv \
    python3-smbus \
    i2c-tools \
    libbluetooth-dev \
    expect \
    nodejs \
    npm \
    nftables

echo "=== Setting up Python virtual environment ==="
python3 -m venv venv --system-site-packages
./venv/bin/pip install --upgrade pip
./venv/bin/pip install \
    flask \
    flask-cors \
    psutil \
    "git+https://github.com/pybluez/pybluez.git#egg=pybluez"

echo "=== Installing Node.js dependencies ==="
cd "$SCRIPT_DIR/server"
npm install

echo "=== Done ==="
