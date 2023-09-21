import bluetooth
import picamera
import time
import subprocess
from datetime import datetime

# List of smartphone Bluetooth addresses (replace with your actual addresses)
TARGET_BT_ADDRESSES = ["XX:XX:XX:XX:XX:XX"]
# List of smartphone MAC addresses (replace with your actual addresses)
TARGET_AP_MAC_ADDRESSES = ["XX:XX:XX:XX:XX:XX"]

# Initialize the camera
camera = picamera.PiCamera()
filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.h264')
camera.start_recording(filename)
recording = True

def update_annotation(camera):
    """Update the annotation text on the camera."""
    camera.annotate_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def is_device_connected_to_bt(bt_addresses):
    """Check if any of the given Bluetooth addresses are visible."""
    for addr in bt_addresses:
        status = bluetooth.lookup_name(addr, timeout=5)
        if status:
            return True
    return False

def is_in_ap_mode():
    """Check if the device is in AP mode."""
    try:
        output = subprocess.check_output("ip addr show wlan0 | grep '192.168.4.1'", shell=True).decode('utf-8').strip()
        return bool(output)
    except Exception:
        return False

def is_device_connected_to_ap(mac_addresses):
    """Check if any of the given MAC addresses are connected to the AP."""
    if not is_in_ap_mode():
        return False

    try:
        output = subprocess.check_output("cat /var/lib/misc/dnsmasq.leases", shell=True).decode('utf-8').strip()
        for mac in mac_addresses:
            if mac in output:
                return True
        return False
    except Exception:
        return False

# Enable timestamp on the video
camera.annotate_background = picamera.Color('black')
update_annotation(camera)

try:
    while True:
        # Update annotation
        update_annotation(camera)

        # Check if any of the smartphones' Bluetooth addresses are connected or if they're connected to the AP
        if is_device_connected_to_bt(TARGET_BT_ADDRESSES) or is_device_connected_to_ap(TARGET_AP_MAC_ADDRESSES):
            if recording:
                print("Device detected. Pausing recording.")
                camera.wait_recording(0)  # Pause recording
                recording = False
        else:
            if not recording:
                print("No devices detected. Resuming recording.")
                camera.wait_recording()  # Resume recording
                recording = True

        print("Waiting for 5 seconds before checking again...")
        time.sleep(5)

except KeyboardInterrupt:
    camera.stop_recording()
    camera.close()
