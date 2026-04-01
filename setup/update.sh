#!/bin/bash

# Update Security-Cam from git and rebuild if needed.
# Compares the current commit with the last-built commit to skip unnecessary rebuilds.
# Designed to be safe as a systemd ExecStartPre - always exits 0 so the service starts
# even if the update/build fails.
#
# Usage:
#   sudo ./setup/update.sh          # Pull, rebuild if changed
#   sudo ./setup/update.sh --force  # Pull and rebuild regardless

PROJECT_DIR="/opt/security-cam"
STAMP_FILE="$PROJECT_DIR/.last-built-commit"
LOG_DIR="$PROJECT_DIR/logs/update"

cd "$PROJECT_DIR"

# --- Set up logging ---
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date '+%Y-%m-%d_%H-%M-%S').log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Keep only the last 20 update logs
ls -1t "$LOG_DIR"/*.log 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null || true

# Fix safe.directory when running as root (service) on a pi-owned repo
git config --global --add safe.directory "$PROJECT_DIR" 2>/dev/null || true

FORCE=false
if [ "$1" = "--force" ]; then
    FORCE=true
fi

# --- Fix ownership so both root (service) and pi (ssh) can use the repo ---
chown -R pi:pi "$PROJECT_DIR/.git" 2>/dev/null || true

# --- Pull latest code as pi user (skip if no internet) ---
echo "=== Pulling latest code ==="
BEFORE=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

sudo -u pi timeout 15 git pull --ff-only 2>/dev/null || {
    echo "Warning: git pull failed (no internet or dirty tree). Continuing with current code."
}

# Merge upstream mediamtx defaults with user's camera settings
echo "=== Syncing MediaMTX config ==="
python3 -c "
import sys; sys.path.insert(0, '$PROJECT_DIR/client')
from modules.mediamtx_helpers import sync_config; sync_config()
" 2>&1 || echo "Warning: MediaMTX config sync failed. Continuing with existing config."

AFTER=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# --- Check if rebuild is needed ---
LAST_BUILT=$(cat "$STAMP_FILE" 2>/dev/null || echo "none")

if [ "$FORCE" = true ]; then
    echo "Forced rebuild requested."
elif [ "$AFTER" = "$LAST_BUILT" ] && [ -d "$PROJECT_DIR/server/dist" ]; then
    echo "Already up to date (commit $AFTER). Skipping rebuild."
    exit 0
else
    echo "New code detected: $BEFORE -> $AFTER"
fi

# --- Install dependencies ---
echo "=== Installing dependencies ==="
if ./install_requirements.sh; then
    # Save commit stamp only on successful build
    echo "$AFTER" > "$STAMP_FILE"
    echo "=== Update complete ==="
else
    echo "Warning: install/build failed. Service will start with previous build."
fi

# Always exit 0 so the service starts even if update failed
exit 0
