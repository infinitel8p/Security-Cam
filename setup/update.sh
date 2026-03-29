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

FORCE=false
if [ "$1" = "--force" ]; then
    FORCE=true
fi

# --- Pull latest code ---
echo "=== Pulling latest code ==="
BEFORE=$(git rev-parse HEAD)
git pull --ff-only || {
    echo "Warning: git pull failed (dirty tree or diverged branch). Continuing with current code."
}
AFTER=$(git rev-parse HEAD)

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
