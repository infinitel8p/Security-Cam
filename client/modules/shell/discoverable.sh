#!/usr/bin/expect -f
#
# Make the Pi discoverable and wait for an incoming pairing request.
# Auto-accepts passkey/service prompts.  Returns the paired device
# address on stdout (last line) or exits 1 if nothing paired.
#
# Usage: discoverable.sh [timeout_seconds]  (default 90)

set timeout_secs [expr {[llength $argv] > 0 ? [lindex $argv 0] : 90}]

# Ensure bluetooth is on
exec sudo rfkill unblock bluetooth 2>/dev/null
exec bluetoothctl power on 2>/dev/null

# Snapshot currently paired devices before we start
set before_paired [exec bluetoothctl devices Paired 2>/dev/null]

log_user 0
set timeout $timeout_secs
spawn bluetoothctl
expect "#"
send "agent on\r"
send "default-agent\r"
send "discoverable on\r"
send "pairable on\r"

expect {
    "Confirm passkey" {
        send "yes\r"
        set timeout 15
        exp_continue
    }
    "Authorize service" {
        send "yes\r"
        set timeout 15
        exp_continue
    }
    "Request confirmation" {
        send "yes\r"
        set timeout 15
        exp_continue
    }
    timeout {}
}

send "discoverable off\r"
sleep 1
send "quit\r"
expect eof

# Compare paired devices to find the newly paired one
set after_paired [exec bluetoothctl devices Paired 2>/dev/null]

# Find new entries
foreach line [split $after_paired "\n"] {
    if {[string first $line $before_paired] == -1 && [regexp {Device ([0-9A-Fa-f:]+) (.+)} $line _ mac name]} {
        # Trust the new device
        exec bluetoothctl trust $mac 2>/dev/null
        puts "PAIRED $mac $name"
        exit 0
    }
}

puts "NO_PAIR"
exit 1
