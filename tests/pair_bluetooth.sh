#!/bin/bash
# Scan for nearby Bluetooth devices and pair with a selected one

echo "Scanning for Bluetooth devices (10 seconds)..."
bluetoothctl power on > /dev/null 2>&1
bluetoothctl agent on > /dev/null 2>&1
bluetoothctl default-agent > /dev/null 2>&1

# Scan for 10 seconds and collect devices
bluetoothctl --timeout 10 scan on > /dev/null 2>&1

# List discovered devices
echo ""
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
bluetoothctl pair "$mac"

echo "Trusting $name ($mac)..."
bluetoothctl trust "$mac"

echo ""
# Verify pairing
if bluetoothctl info "$mac" 2>/dev/null | grep -q "Paired: yes"; then
    echo "Done! $name ($mac) is paired and trusted."
else
    echo "Warning: Pairing may have failed. Check manually with: bluetoothctl info $mac"
fi
