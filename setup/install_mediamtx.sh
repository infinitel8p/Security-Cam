#!/bin/bash
set -e

# Install MediaMTX for Raspberry Pi
# Downloads the binary, verifies checksum, and sets up the systemd service.
# Safe to re-run (idempotent).
#
# Usage:
#   ./install_mediamtx.sh           # Install pinned version (tested)
#   ./install_mediamtx.sh --latest  # Install latest release from GitHub

MEDIAMTX_VERSION="v1.17.0"
INSTALL_DIR="/usr/local/bin"
SERVICE_FILE="/etc/systemd/system/mediamtx.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Known SHA256 checksums for v1.17.0
declare -A CHECKSUMS=(
    ["linux_arm64"]="09610ea1d4a6489a97bedd9cabd62e0ef7ce2d040389d270c31ba51727732b5b"
    ["linux_armv7"]="23f3b97babb6f772453910652e5139b7cb6d7ec64ff763ad15828c7974e18818"
    ["linux_armv6"]="2f1278939b4cd6a6c49bae7408eeea15a974073a01fcdd4a9bc9d640e5b94006"
    ["linux_amd64"]="97165888845f3a0a9bfeaa4b34bd19d72aa3f8d9abd39f9a02042c9fa434fb5a"
)

echo "=== Installing MediaMTX ==="

# Detect architecture
ARCH=$(uname -m)
case "$ARCH" in
    aarch64) MTX_ARCH="linux_arm64" ;;
    armv7l)  MTX_ARCH="linux_armv7" ;;
    armv6l)  MTX_ARCH="linux_armv6" ;;
    x86_64)  MTX_ARCH="linux_amd64" ;;
    *)
        echo "Error: unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Check if already installed
if command -v mediamtx &>/dev/null; then
    CURRENT_VERSION=$(mediamtx --version 2>&1 | head -1 || echo "unknown")
    echo "MediaMTX already installed: $CURRENT_VERSION"
    read -p "Re-install/update? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping binary install, updating service file only..."
        SKIP_BINARY=true
    fi
fi

if [ "$SKIP_BINARY" != "true" ]; then
    # Determine version to install
    if [ "$1" = "--latest" ]; then
        echo "Fetching latest MediaMTX version..."
        VERSION=$(curl -s https://api.github.com/repos/bluenviron/mediamtx/releases/latest | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
        if [ -z "$VERSION" ]; then
            echo "Error: could not determine latest version. Check your internet connection."
            exit 1
        fi
        echo "Latest version: $VERSION"
    else
        VERSION="$MEDIAMTX_VERSION"
        echo "Pinned version: $VERSION"
    fi

    FILENAME="mediamtx_${VERSION}_${MTX_ARCH}.tar.gz"
    DOWNLOAD_URL="https://github.com/bluenviron/mediamtx/releases/download/${VERSION}/${FILENAME}"

    # Download
    TMPDIR=$(mktemp -d)
    echo "Downloading $DOWNLOAD_URL ..."
    curl -L -o "$TMPDIR/$FILENAME" "$DOWNLOAD_URL"

    # Verify checksum (only for pinned version with known checksums)
    EXPECTED_SHA="${CHECKSUMS[$MTX_ARCH]}"
    if [ -n "$EXPECTED_SHA" ] && [ "$VERSION" = "$MEDIAMTX_VERSION" ]; then
        echo "Verifying SHA256 checksum..."
        ACTUAL_SHA=$(sha256sum "$TMPDIR/$FILENAME" | awk '{print $1}')
        if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
            echo "Error: checksum mismatch!"
            echo "  Expected: $EXPECTED_SHA"
            echo "  Got:      $ACTUAL_SHA"
            rm -rf "$TMPDIR"
            exit 1
        fi
        echo "Checksum OK"
    elif [ "$VERSION" != "$MEDIAMTX_VERSION" ]; then
        echo "Warning: skipping checksum verification (no known checksums for $VERSION)"
    fi

    # Install
    tar -xzf "$TMPDIR/$FILENAME" -C "$TMPDIR"
    sudo mv "$TMPDIR/mediamtx" "$INSTALL_DIR/mediamtx"
    sudo chmod +x "$INSTALL_DIR/mediamtx"
    rm -rf "$TMPDIR"

    echo "Installed mediamtx to $INSTALL_DIR/mediamtx"
    mediamtx --version
fi

# Install systemd service
echo "Installing systemd service..."
sudo cp "$REPO_ROOT/client/data/mediamtx.service" "$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable mediamtx.service

echo ""
echo "=== MediaMTX installed ==="
echo "Config:  $REPO_ROOT/client/data/mediamtx.yml"
echo "Service: $SERVICE_FILE"
echo ""
echo "Commands:"
echo "  sudo systemctl start mediamtx    # Start now"
echo "  sudo systemctl status mediamtx   # Check status"
echo "  sudo systemctl restart mediamtx  # Restart"
echo "  journalctl -u mediamtx -f        # View logs"
