#!/usr/bin/expect -f

set address [lindex $argv 0]

spawn sudo bluetoothctl
expect "#"
send "agent NoInputNoOutput\r"
expect "#"
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

        # Wait up to 20 seconds for the device to appear
        set timeout 20
        expect {
            -re "Device $address" {
                puts "Device found, proceeding with pairing..."
                send "scan off\r"
                expect "Controller"
                send "pair $address\r"
                expect {
                    "Request confirmation" {
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
                puts "Device not found within 20 seconds, aborting."
                send "scan off\r"
                exit 1
            }
        }
    }
}

# Trust the device
sleep 2
send "trust $address\r"
sleep 2
send "quit\r"
expect eof
