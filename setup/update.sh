#!/bin/bash

# Update Security-Cam from git and rebuild if needed.
# Compares the current commit with the last-built commit to skip unnecessary rebuilds.
# Designed to be safe as a systemd ExecStartPre — always exits 0 so the service starts
# even if the update/build fails.
#
# Usage:
#   sudo ./setup/update.sh          # Pull, rebuild if changed
#   sudo ./setup/update.sh --force  # Pull and rebuild regardless

PROJECT_DIR="/opt/security-cam"
STAMP_FILE="$PROJECT_DIR/.last-built-commit"

cd "$PROJECT_DIR"

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

# Stash any local changes (e.g. runtime-modified files not yet in .gitignore)
sudo -u pi git stash -q 2>/dev/null || true

sudo -u pi timeout 15 git pull --ff-only 2>/dev/null || {
    echo "Warning: git pull failed (no internet or dirty tree). Continuing with current code."
}

# Restore stashed changes (local settings take priority over repo)
sudo -u pi git stash pop -q 2>/dev/null || true

AFTER=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# --- Check if rebuild is needed ---
LAST_BUILT=$(cat "$STAMP_FILE" 2>/dev/null || echo "none")

if [ "$FORCE" = true ]; then
    echo "Forced rebuild requested."
elif [ "$AFTER" = "$LAST_BUILT" ]; then
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
