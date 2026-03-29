#!/bin/bash
# Scan for nearby Bluetooth devices and pair with a selected one

# Ensure Bluetooth is unblocked and powered on
sudo rfkill unblock bluetooth > /dev/null 2>&1
bluetoothctl power on > /dev/null 2>&1

echo "Bluetooth Pairing Script"
echo "========================"
echo ""
echo "  [1] Scan for devices (Pi finds your device)"
echo "  [2] Wait for incoming pairing (your device finds the Pi)"
echo ""
read -p "Choose mode (1/2): " mode

if [ "$mode" = "2" ]; then
    echo ""
    echo "Making Pi discoverable and waiting for incoming pairing requests..."
    echo "On your device, open Bluetooth settings and tap 'securitycam' to pair."
    echo "Press Ctrl+C to stop waiting."
    echo ""

    # Use expect to make Pi discoverable and wait for pairing
    expect <<'WAIT_EOF'
    set timeout 120
    spawn bluetoothctl
    expect "Agent registered"
    send "agent on\r"
    send "default-agent\r"
    send "discoverable on\r"
    send "pairable on\r"
    expect {
        -re "Confirm passkey (\\d+)" {
            send "yes\r"
            exp_continue
        }
        "Paired: yes" {
            sleep 2
        }
        timeout {
            puts "\nNo pairing request received within 2 minutes."
        }
    }
    send "discoverable off\r"
    sleep 1
    send "exit\r"
    expect eof
WAIT_EOF

    # Trust the most recently paired device
    last_paired=$(bluetoothctl devices Paired | tail -1)
    if [ -n "$last_paired" ]; then
        mac=$(echo "$last_paired" | awk '{print $2}')
        name=$(echo "$last_paired" | cut -d' ' -f3-)
        bluetoothctl trust "$mac" > /dev/null 2>&1
        echo ""
        echo "Done! $name ($mac) is paired and trusted."
    else
        echo ""
        echo "No device was paired."
    fi
    exit 0
fi

# Mode 1: Scan for devices
echo ""
echo "Scanning for Bluetooth devices (30 seconds)..."
echo "Tip: On iPhone, keep Settings > Bluetooth open during the scan."
echo ""

# Use expect to run an interactive bluetoothctl session for scanning
expect <<'SCAN_EOF' > /dev/null 2>&1
set timeout 35
spawn bluetoothctl
expect "Agent registered"
send "agent on\r"
send "default-agent\r"
send "scan on\r"
sleep 30
send "scan off\r"
sleep 1
send "exit\r"
expect eof
SCAN_EOF

# List discovered devices
echo "Discovered devices:"
echo "-------------------"
mapfile -t devices < <(bluetoothctl devices | grep "^Device")

if [ ${#devices[@]} -eq 0 ]; then
    echo "No devices found. Make sure your device's Bluetooth visibility is turned on."
    exit 1
fi

for i in "${!devices[@]}"; do
    echo "  [$i] ${devices[$i]#Device }"
done

echo ""
read -p "Enter the number of the device to pair with (or 'q' to quit): " choice

if [ "$choice" = "q" ]; then
    exit 0
fi

if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -ge ${#devices[@]} ]; then
    echo "Invalid selection."
    exit 1
fi

# Extract MAC address
mac=$(echo "${devices[$choice]}" | awk '{print $2}')
name=$(echo "${devices[$choice]}" | cut -d' ' -f3-)

echo ""
echo "Pairing with $name ($mac)..."

# Use expect to pair and trust in an interactive session
expect <<PAIR_EOF
set timeout 30
spawn bluetoothctl
expect "Agent registered"
send "agent on\r"
send "default-agent\r"
send "pair $mac\r"
expect {
    "Confirm passkey" {
        send "yes\r"
        expect "Pairing successful"
    }
    "Pairing successful" {}
    timeout {
        puts "Pairing timed out"
        exit 1
    }
}
send "trust $mac\r"
expect "trust succeeded"
send "exit\r"
expect eof
PAIR_EOF

echo ""
# Verify pairing
if bluetoothctl info "$mac" 2>/dev/null | grep -q "Paired: yes"; then
    echo "Done! $name ($mac) is paired and trusted."
else
    echo "Warning: Pairing may have failed. Check manually with: bluetoothctl info $mac"
fi
