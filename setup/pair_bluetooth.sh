#!/bin/bash
# Scan for nearby Bluetooth devices and pair with a selected one

# Ensure Bluetooth is unblocked and powered on
sudo rfkill unblock bluetooth > /dev/null 2>&1
bluetoothctl power on > /dev/null 2>&1

run_scan_mode() {
    echo ""
    echo "=== Mode 1: Scan for devices ==="
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
send "quit\r"
expect eof
SCAN_EOF

    # List discovered devices
    echo "Discovered devices:"
    echo "-------------------"
    mapfile -t devices < <(bluetoothctl devices | grep "^Device")

    if [ ${#devices[@]} -eq 0 ]; then
        echo "No devices found. Make sure your device's Bluetooth visibility is turned on."
        return 1
    fi

    for i in "${!devices[@]}"; do
        echo "  [$i] ${devices[$i]#Device }"
    done

    echo ""
    read -p "Enter the number of the device to pair with (or 'q' to go back): " choice

    if [ "$choice" = "q" ]; then
        return 1
    fi

    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -ge ${#devices[@]} ]; then
        echo "Invalid selection."
        return 1
    fi

    # Extract MAC address
    mac=$(echo "${devices[$choice]}" | awk '{print $2}')
    name=$(echo "${devices[$choice]}" | cut -d' ' -f3-)

    echo ""
    echo "Pairing with $name ($mac)..."
    echo "A confirmation prompt may appear on your device — please accept it."
    echo ""

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
    "Authorize service" {
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
send "quit\r"
expect eof
PAIR_EOF

    echo ""
    if bluetoothctl info "$mac" 2>/dev/null | grep -q "Paired: yes"; then
        echo "Done! $name ($mac) is paired and trusted."
        return 0
    else
        echo "Pairing may have failed. Check manually with: bluetoothctl info $mac"
        return 1
    fi
}

run_wait_mode() {
    echo ""
    echo "=== Mode 2: Wait for incoming pairing ==="
    echo "The Pi is now discoverable."
    echo "On your device, open Bluetooth settings and pair with the Pi."
    echo "Waiting for incoming pairing request (120 seconds)..."
    echo "A confirmation prompt may appear on your device — please accept it."
    echo ""

    # Use expect to make Pi discoverable and wait for pairing
    # log_user 0 hides the spam, but send_user prints our custom status updates
    expect <<'WAIT_EOF'
log_user 0
set timeout 120
spawn bluetoothctl
expect "Agent registered"
send "agent on\r"
send "default-agent\r"
send "discoverable on\r"
send "pairable on\r"

expect {
    "Confirm passkey" {
        puts ">>> Passkey prompt detected. Auto-confirming..."
        send "yes\r"
        exp_continue
    }
    "Authorize service" {
        puts ">>> Service authorization requested. Auto-approving..."
        send "yes\r"
        exp_continue
    }
    -re "(Paired: yes|Pairing successful|ServicesResolved: yes)" {
        puts ">>> Success condition met! Finalizing connection..."
        send "discoverable off\r"
        send "quit\r"
    }
    timeout {
        puts "\n>>> No pairing request received within 120 seconds."
        send "quit\r"
    }
}
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
        return 0
    else
        echo ""
        echo "No new device was paired."
        return 1
    fi
}

# Main loop
while true; do
    echo "Bluetooth Pairing Script"
    echo "========================"
    echo ""
    echo "  [1] Scan for devices (Pi finds your device)"
    echo "  [2] Wait for incoming pairing (your device finds the Pi)"
    echo "  [q] Quit"
    echo ""
    read -p "Choose an option: " mode

    case "$mode" in
        1)
            run_scan_mode
            result=$?
            if [ $result -eq 0 ]; then
                exit 0
            else
                echo ""
                echo "---"
                echo "You can try again or switch to the other mode."
                echo ""
            fi
            ;;
        2)
            run_wait_mode
            result=$?
            if [ $result -eq 0 ]; then
                exit 0
            else
                echo ""
                echo "---"
                echo "You can try again or switch to the other mode."
                echo ""
            fi
            ;;
        q)
            echo "Bye!"
            exit 0
            ;;
        *)
            echo "Invalid option."
            echo ""
            ;;
    esac
done
