#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root."
  exit
fi

# Step 1: Install Required Packages
echo "Installing required packages..."
apt-get update
apt-get install -y hostapd dnsmasq

# Step 2: Create the Switching Script
echo "Creating the switching script..."
cat <<EOL > /usr/local/bin/wifi_switcher.sh
#!/bin/bash
echo "--- $(date) - Script started with PID $$  ---" >> /tmp/wifi_switcher.log

# Define an array of SSIDs
HOME_SSIDS=('YOUR_HOME_WIFI_SSID1')

# Initialize a flag to indicate if a home network is found
home_network_found=0

# Delay for 180 seconds
echo "$(date) - Initialization done. Sleeping for 2 min before running." >> /tmp/wifi_switcher.log
sleep 180

# Check for home networks
echo "$(date) - Checking for home networks" >> /tmp/wifi_switcher.log

# Scan for available networks and save the results to a variable
scan_results=$(sudo iwlist wlan0 scan | grep ESSID)

# Log the scan results and iwconfig output
echo "$scan_results" >> /tmp/wifi_switcher.log

# Check the scan results for each SSID in the HOME_SSIDS array
for ssid in "${HOME_SSIDS[@]}"; do
    echo "$scan_results" | grep -q "$ssid"
    if [ $? -eq 0 ]; then
        home_network_found=1
        break
    fi
done

if [ $home_network_found -eq 1 ]; then
    # Home network found
    echo "$(date) - Home network found. Stopping services." >> /tmp/wifi_switcher.log
    sudo systemctl stop hostapd
    sudo systemctl stop dnsmasq
else
    # Home network not found, start AP mode
    echo "$(date) - Home network not found. Starting services." >> /tmp/wifi_switcher.log
    sudo systemctl start hostapd
    sudo systemctl start dnsmasq
fi

echo "--- $(date) - Script finished ---" >> /tmp/wifi_switcher.log
EOL

chmod +x /usr/local/bin/wifi_switcher.sh

# Step 2.2: Schedule the Script with Cron
(crontab -l 2>/dev/null; echo "*/4 * * * * sudo /usr/local/bin/wifi_switcher.sh") | crontab -

# Step 3: Configure Hostapd for AP Mode
echo "Configuring Hostapd..."
cat <<EOL > /etc/hostapd/hostapd.conf
interface=wlan0
driver=nl80211
ssid=DevAccessPoint
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=YOUR_AP_PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOL

sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

# Step 4: Configure Dnsmasq for DHCP in AP Mode
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
cat <<EOL > /etc/dnsmasq.conf
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOL

# Step 5: Configure a Static IP for the wlan0 Interface
cat <<EOL >> /etc/dhcpcd.conf
# Use a static IP for AP mode
profile static_ap
static ip_address=192.168.4.1/24

# Set the profile based on the SSID
interface wlan0
ssid DevAccessPoint
use_profile static_ap
EOL

# Step 6: Restart the Services
systemctl restart dnsmasq
systemctl restart hostapd

# Handle potential hostapd errors
systemctl unmask hostapd
systemctl enable hostapd

echo "Configuration complete!"
