#!/bin/bash
set -e

# Setup WiFi Access Point using hostapd + dnsmasq
# Creates a virtual ap0 interface on the Pi's WiFi chip and runs an AP alongside
# the normal WiFi connection. Both must share the same channel.
#
# Prerequisites:
#   - Raspberry Pi connected to WiFi via wlan0
#   - Run as root or with sudo
#
# Usage:
#   ./setup_ap.sh                          # Interactive (prompts for SSID, password, channel)
#   ./setup_ap.sh --ssid MyAP --password secret123 --channel 6  # Non-interactive

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$REPO_ROOT/client/data"

AP_INTERFACE="ap0"
AP_IP="192.168.4.1"
AP_NETMASK="24"

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --ssid)     AP_SSID="$2"; shift 2 ;;
        --password) AP_PASSWORD="$2"; shift 2 ;;
        --channel)  AP_CHANNEL="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--ssid NAME] [--password PASS] [--channel N]"
            echo ""
            echo "Sets up a WiFi Access Point on the Raspberry Pi using hostapd."
            echo "If arguments are omitted, you will be prompted interactively."
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# --- Detect current WiFi channel ---
CURRENT_CHANNEL=$(iw dev wlan0 info 2>/dev/null | grep channel | awk '{print $2}')
if [ -z "$CURRENT_CHANNEL" ]; then
    echo "Warning: could not detect wlan0 channel. Make sure WiFi is connected."
    CURRENT_CHANNEL="6"
fi

# --- Interactive prompts for missing values ---
if [ -z "$AP_SSID" ]; then
    read -p "Access Point SSID [SecurityCam]: " AP_SSID
    AP_SSID="${AP_SSID:-SecurityCam}"
fi

if [ -z "$AP_PASSWORD" ]; then
    while true; do
        read -s -p "Access Point password (min 8 characters): " AP_PASSWORD
        echo
        if [ ${#AP_PASSWORD} -ge 8 ]; then
            break
        fi
        echo "Password must be at least 8 characters."
    done
fi

if [ -z "$AP_CHANNEL" ]; then
    read -p "WiFi channel [${CURRENT_CHANNEL}]: " AP_CHANNEL
    AP_CHANNEL="${AP_CHANNEL:-$CURRENT_CHANNEL}"
fi

echo ""
echo "=== Setting up WiFi Access Point ==="
echo "  SSID:      $AP_SSID"
echo "  Channel:   $AP_CHANNEL"
echo "  Interface: $AP_INTERFACE"
echo "  IP:        $AP_IP/$AP_NETMASK"
echo ""

# --- Install dependencies ---
echo "Installing hostapd and dnsmasq..."
sudo apt-get update -qq
sudo apt-get install -y hostapd dnsmasq

# --- Remove any conflicting NetworkManager AP connection ---
if nmcli connection show SecurityCamAP &>/dev/null; then
    echo "Removing old NetworkManager AP connection..."
    sudo nmcli connection delete SecurityCamAP
fi

# --- Tell NetworkManager to ignore ap0 ---
echo "Configuring NetworkManager to ignore $AP_INTERFACE..."
sudo tee /etc/NetworkManager/conf.d/ignore-ap0.conf > /dev/null << EOF
[keyfile]
unmanaged-devices=interface-name:$AP_INTERFACE
EOF
sudo systemctl reload NetworkManager

# --- Install create-ap0 service ---
echo "Installing create-ap0 systemd service..."
sudo cp "$DATA_DIR/create-ap0.service" /etc/systemd/system/create-ap0.service
sudo systemctl daemon-reload
sudo systemctl enable create-ap0.service

# Recreate the interface cleanly to ensure no leftover wpa_supplicant attachment
echo "Recreating $AP_INTERFACE interface..."
sudo iw dev "$AP_INTERFACE" del 2>/dev/null || true
sudo iw dev wlan0 interface add "$AP_INTERFACE" type __ap

# --- Configure static IP for ap0 ---
echo "Configuring static IP for $AP_INTERFACE..."
sudo tee /etc/systemd/network/10-ap0.network > /dev/null << EOF
[Match]
Name=$AP_INTERFACE

[Network]
Address=$AP_IP/$AP_NETMASK
EOF
sudo systemctl enable systemd-networkd

# --- Configure hostapd ---
echo "Configuring hostapd..."
sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=$AP_INTERFACE
driver=nl80211
ssid=$AP_SSID
hw_mode=g
channel=$AP_CHANNEL
wmm_enabled=0
auth_algs=1
wpa=2
wpa_passphrase=$AP_PASSWORD
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

# Point hostapd daemon config to our conf file
sudo tee /etc/default/hostapd > /dev/null << 'EOF'
DAEMON_CONF="/etc/hostapd/hostapd.conf"
EOF

# --- Configure dnsmasq ---
echo "Configuring dnsmasq for $AP_INTERFACE..."
sudo cp "$DATA_DIR/dnsmasq-ap0.conf" /etc/dnsmasq.d/ap0.conf

# --- Enable and start services ---
echo "Enabling services..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Release ap0 from any leftover wpa_supplicant attachment (NM retry loops can leave it held)
sudo pkill -f "wpa_supplicant.*$AP_INTERFACE" 2>/dev/null || true
sleep 1

# Set IP and start now
sudo ip addr flush dev "$AP_INTERFACE" 2>/dev/null || true
sudo ip addr add "$AP_IP/$AP_NETMASK" dev "$AP_INTERFACE" 2>/dev/null || true
sudo ip link set "$AP_INTERFACE" up

echo "Starting hostapd..."
sudo systemctl restart hostapd

echo "Starting dnsmasq..."
sudo systemctl restart dnsmasq

# --- Verify ---
echo ""
if sudo systemctl is-active --quiet hostapd; then
    echo "=== Access Point is running ==="
    echo "  SSID:     $AP_SSID"
    echo "  IP:       $AP_IP"
    echo "  SSH:      ssh pi@$AP_IP"
    echo ""
    echo "Commands:"
    echo "  sudo systemctl status hostapd    # Check AP status"
    echo "  sudo systemctl restart hostapd   # Restart AP"
    echo "  journalctl -u hostapd -f         # View AP logs"
else
    echo "=== ERROR: hostapd failed to start ==="
    echo "Check logs: journalctl -u hostapd --no-pager -l"
    exit 1
fi
