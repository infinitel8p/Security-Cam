#!/bin/bash
set -e

# Setup WiFi Access Point using hostapd + dnsmasq
# Creates a virtual ap0 interface on the Pi's WiFi chip and runs an AP alongside
# the normal WiFi connection. Both must share the same channel.
#
# Prerequisites:
#   - Raspberry Pi connected to WiFi via wlan0
#   - Run with sudo
#
# Usage:
#   sudo ./setup_ap.sh                          # Interactive (prompts for SSID, password, channel)
#   sudo ./setup_ap.sh --ssid MyAP --password secret123 --channel 6  # Non-interactive

if [ "$EUID" -ne 0 ]; then
    echo "Error: this script must be run with sudo"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$REPO_ROOT/client/data"

# --- Set up logging ---
LOG_DIR="$REPO_ROOT/logs/ap-setup"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date '+%Y-%m-%d_%H-%M-%S').log"
exec > >(tee -a "$LOG_FILE") 2>&1
ls -1t "$LOG_DIR"/*.log 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null || true

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
            echo "Usage: sudo $0 [--ssid NAME] [--password PASS] [--channel N]"
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
echo "Installing hostapd, dnsmasq, and iptables..."
apt-get update -qq
apt-get install -y hostapd dnsmasq iptables

# --- Remove any conflicting NetworkManager AP connection ---
if nmcli connection show SecurityCamAP &>/dev/null; then
    echo "Removing old NetworkManager AP connection..."
    nmcli connection delete SecurityCamAP
fi

# --- Tell NetworkManager to ignore ap0 ---
echo "Configuring NetworkManager to ignore $AP_INTERFACE..."
mkdir -p /etc/NetworkManager/conf.d
tee /etc/NetworkManager/conf.d/ignore-ap0.conf > /dev/null << EOF
[keyfile]
unmanaged-devices=interface-name:$AP_INTERFACE
EOF
systemctl reload NetworkManager

# --- Install create-ap0 service ---
echo "Installing create-ap0 systemd service..."
cp "$DATA_DIR/create-ap0.service" /etc/systemd/system/create-ap0.service
systemctl daemon-reload
systemctl enable create-ap0.service

# Recreate the interface cleanly to ensure no leftover wpa_supplicant attachment
echo "Recreating $AP_INTERFACE interface..."
iw dev "$AP_INTERFACE" del 2>/dev/null || true
iw dev wlan0 interface add "$AP_INTERFACE" type __ap

# --- Configure hostapd ---
echo "Configuring hostapd..."
tee /etc/hostapd/hostapd.conf > /dev/null << EOF
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

# Point hostapd daemon to our conf file and suppress DAEMON_OPTS warning
tee /etc/default/hostapd > /dev/null << 'EOF'
DAEMON_CONF="/etc/hostapd/hostapd.conf"
DAEMON_OPTS=""
EOF

# Ensure hostapd starts after ap0 is created
mkdir -p /etc/systemd/system/hostapd.service.d
tee /etc/systemd/system/hostapd.service.d/after-ap0.conf > /dev/null << 'EOF'
[Unit]
After=create-ap0.service
Requires=create-ap0.service
EOF

# --- Configure dnsmasq ---
echo "Configuring dnsmasq for $AP_INTERFACE..."
cp "$DATA_DIR/dnsmasq-ap0.conf" /etc/dnsmasq.d/ap0.conf

# Ensure dnsmasq starts after hostapd (so ap0 has an IP)
mkdir -p /etc/systemd/system/dnsmasq.service.d
tee /etc/systemd/system/dnsmasq.service.d/after-hostapd.conf > /dev/null << 'EOF'
[Unit]
After=hostapd.service
Requires=hostapd.service
EOF

# --- Configure static IP for ap0 via networkd (scoped to ap0 only) ---
echo "Configuring static IP for $AP_INTERFACE..."
mkdir -p /etc/systemd/network
tee /etc/systemd/network/10-ap0.network > /dev/null << EOF
[Match]
Name=$AP_INTERFACE

[Network]
Address=$AP_IP/$AP_NETMASK
EOF

# Enable networkd but ensure it doesn't interfere with NM-managed interfaces
systemctl enable systemd-networkd
systemctl restart systemd-networkd

# --- Enable and start services ---
echo "Enabling services..."
systemctl daemon-reload
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq

# Set IP and bring interface up
ip addr flush dev "$AP_INTERFACE" 2>/dev/null || true
ip addr add "$AP_IP/$AP_NETMASK" dev "$AP_INTERFACE" 2>/dev/null || true
ip link set "$AP_INTERFACE" up

echo "Starting hostapd..."
systemctl restart hostapd
sleep 2

echo "Starting dnsmasq..."
systemctl restart dnsmasq

# --- Enable IP forwarding and NAT for internet passthrough ---
echo "Enabling IP forwarding and NAT (ap0 → wlan0)..."
sysctl -w net.ipv4.ip_forward=1

# Persist across reboots
if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi

# NAT: masquerade traffic from AP clients going out through wlan0
iptables -t nat -C POSTROUTING -o wlan0 -j MASQUERADE 2>/dev/null || \
    iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE

# Allow forwarding between interfaces
iptables -C FORWARD -i "$AP_INTERFACE" -o wlan0 -j ACCEPT 2>/dev/null || \
    iptables -A FORWARD -i "$AP_INTERFACE" -o wlan0 -j ACCEPT
iptables -C FORWARD -i wlan0 -o "$AP_INTERFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
    iptables -A FORWARD -i wlan0 -o "$AP_INTERFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT

# Captive portal: redirect HTTP (port 80) on AP to the dashboard (port 3000)
iptables -t nat -C PREROUTING -i "$AP_INTERFACE" -p tcp --dport 80 -j REDIRECT --to-port 3000 2>/dev/null || \
    iptables -t nat -A PREROUTING -i "$AP_INTERFACE" -p tcp --dport 80 -j REDIRECT --to-port 3000

# Persist iptables rules across reboots
if command -v netfilter-persistent &>/dev/null; then
    netfilter-persistent save
else
    echo "Installing iptables-persistent for rule persistence..."
    DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
    netfilter-persistent save
fi

# --- Verify ---
echo ""
if systemctl is-active --quiet hostapd; then
    echo "=== Access Point is running ==="
    echo "  SSID:        $AP_SSID"
    echo "  IP:          $AP_IP"
    echo "  Dashboard:   http://dashboard.cam  (or http://$AP_IP:3000)"
    echo "  SSH:         ssh pi@$AP_IP"
    echo ""
    echo "  Captive portal enabled - devices auto-open the dashboard on connect."
    echo "  Internet passthrough enabled - AP clients share the Pi's WiFi."
    echo ""
    echo "Commands:"
    echo "  sudo systemctl status hostapd    # Check AP status"
    echo "  sudo systemctl restart hostapd   # Restart AP"
    echo "  journalctl -u hostapd -f         # View AP logs"
    echo ""
    echo "Reboot to verify persistence: sudo reboot"
else
    echo "=== ERROR: hostapd failed to start ==="
    echo ""
    journalctl -u hostapd --no-pager -n 10
    echo ""
    echo "Common fixes:"
    echo "  - Channel mismatch: check 'iw dev' and update /etc/hostapd/hostapd.conf"
    echo "  - Interface held: try 'sudo iw dev ap0 del && sudo iw dev wlan0 interface add ap0 type __ap'"
    exit 1
fi
