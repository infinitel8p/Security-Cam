#!/usr/bin/expect -f

set address [lindex $argv 0]

spawn sudo bluetoothctl
expect "#"
send "remove $address\r"
expect {
    "Device has been removed" {
        puts "Unpairing successful"
    }
    "not available" {
        puts "Device not found or already unpaired"
        exit 1
    }
    timeout {
        puts "Unpairing timeout"
        exit 1
    }
    eof {
        puts "Unexpected EOF"
        exit 1
    }
}
send "quit\r"
expect eof
