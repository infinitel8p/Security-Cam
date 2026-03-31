#!/usr/bin/expect -f

set address [lindex $argv 0]

spawn bluetoothctl
expect "Agent registered"
send "agent on\r"
send "default-agent\r"

# Check if the device is already paired
send "devices Paired\r"
expect {
    -re "$address" {
        # If the device is already paired, skip the pairing process
        puts "Device is already paired, skipping pairing..."
    }
    timeout {
        # If the device is not paired, proceed to scan and pair it
        puts "Device not paired, proceeding with scan and pairing..."
        send "scan on\r"

        # Wait up to 30 seconds for the device to appear
        set timeout 30
        expect {
            -re "Device $address" {
                puts "Device found, proceeding with pairing..."
                send "scan off\r"
                expect "Discovery stopped"
                send "pair $address\r"
                expect {
                    "Confirm passkey" {
                        send "yes\r"
                        expect "Pairing successful"
                    }
                    "Request confirmation" {
                        send "yes\r"
                        expect "Pairing successful"
                    }
                    "Authorize service" {
                        send "yes\r"
                        exp_continue
                    }
                    "Pairing successful" {
                        puts "Pairing successful"
                    }
                    "Failed to pair: org.bluez.Error.AlreadyExists" {
                        puts "Device is already paired, skipping pairing..."
                    }
                    "Failed to pair" {
                        puts "Pairing failed"
                        exit 1
                    }
                    timeout {
                        puts "Pairing timeout"
                        exit 1
                    }
                    eof {
                        puts "Unexpected EOF"
                        exit 1
                    }
                }
            }
            timeout {
                puts "Device not found within 30 seconds, aborting."
                send "scan off\r"
                exit 1
            }
        }
    }
}

# Trust the device
sleep 2
send "trust $address\r"
expect "trust succeeded"
sleep 1
send "quit\r"
expect eof
