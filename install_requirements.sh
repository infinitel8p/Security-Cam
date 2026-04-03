#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# --- Parse flags ---
FORCE=false
NO_LOG=false
for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=true ;;
        --no-log) NO_LOG=true ;;
    esac
done

# --- Set up logging (skip when called from update.sh which logs already) ---
if ! $NO_LOG; then
    LOG_DIR="$SCRIPT_DIR/logs/install"
    mkdir -p "$LOG_DIR"
    LOG_FILE="$LOG_DIR/$(date '+%Y-%m-%d_%H-%M-%S').log"
    exec > >(tee -a "$LOG_FILE") 2>&1
    ls -1t "$LOG_DIR"/*.log 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null || true
fi

# --- Fingerprint helpers ---
# Generate a hash of the inputs for a given step so we can skip it when unchanged.
STAMP_DIR="$SCRIPT_DIR/.install_stamps"
mkdir -p "$STAMP_DIR"

step_changed() {
    local name="$1"
    local current_hash="$2"
    local stamp_file="$STAMP_DIR/$name"
    if $FORCE; then return 0; fi
    if [ -f "$stamp_file" ] && [ "$(cat "$stamp_file")" = "$current_hash" ]; then
        return 1  # unchanged
    fi
    return 0  # changed
}

stamp_step() {
    local name="$1"
    local current_hash="$2"
    echo "$current_hash" > "$STAMP_DIR/$name"
}

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
APT_HASH=$(md5sum "$SCRIPT_DIR/required-apt-packages.txt" | cut -d' ' -f1)
if step_changed "apt" "$APT_HASH"; then
    echo "=== Installing system packages ==="
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $(grep -v '^\s*#' "$SCRIPT_DIR/required-apt-packages.txt" | grep -v '^\s*$')
    stamp_step "apt" "$APT_HASH"
else
    echo "=== System packages unchanged, skipping ==="
fi

# --- Python virtual environment ---
REQ_HASH=$(md5sum "$SCRIPT_DIR/requirements.txt" | cut -d' ' -f1)
if step_changed "pip" "$REQ_HASH"; then
    echo "=== Setting up Python virtual environment ==="
    python3 -m venv venv --system-site-packages
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r "$SCRIPT_DIR/requirements.txt"
    stamp_step "pip" "$REQ_HASH"
else
    echo "=== Python packages unchanged, skipping ==="
fi

# --- Frontend ---
cd "$SCRIPT_DIR/server"

# Hash package-lock + all source files to detect when a rebuild is needed
NPM_HASH=$(md5sum "$SCRIPT_DIR/server/package-lock.json" 2>/dev/null | cut -d' ' -f1)
if step_changed "npm" "$NPM_HASH"; then
    echo "=== Installing Node.js dependencies ==="
    sudo -u pi npm install
    stamp_step "npm" "$NPM_HASH"
else
    echo "=== Node.js dependencies unchanged, skipping ==="
fi

# Hash all frontend source files (src/, public/, config files)
FRONTEND_HASH=$(find "$SCRIPT_DIR/server/src" "$SCRIPT_DIR/server/public" \
    "$SCRIPT_DIR/server/astro.config.mjs" "$SCRIPT_DIR/server/tsconfig.json" \
    "$SCRIPT_DIR/server/package.json" \
    -type f -print0 2>/dev/null | sort -z | xargs -0 md5sum 2>/dev/null | md5sum | cut -d' ' -f1)

if step_changed "build" "$FRONTEND_HASH"; then
    echo "=== Building frontend ==="
    # Limit Node heap to prevent OOM on Pi Zero 2 W (416MB total RAM).
    # Build to a temp directory so a failed build doesn't destroy the previous one.
    export NODE_OPTIONS="--max-old-space-size=256"
    sudo -u pi npx astro build --outDir dist_new
    rm -rf dist
    mv dist_new dist
    stamp_step "build" "$FRONTEND_HASH"
else
    echo "=== Frontend unchanged, skipping build ==="
fi

echo "=== Done ==="
