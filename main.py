import bluetooth
import picamera
import time
import subprocess
from datetime import datetime
import logging
import json
import os
from dotenv import load_dotenv

# Set up logging with custom timestamp format
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S')

# Try to load config from .env file
logging.info("Loading config from .env file...")
load_dotenv()

TARGET_BT_ADDRESSES = os.getenv("TARGET_BT_ADDRESSES")
TARGET_AP_MAC_ADDRESSES = os.getenv("TARGET_AP_MAC_ADDRESSES")

# If not found in .env, fall back to config.json
if not TARGET_BT_ADDRESSES or not TARGET_AP_MAC_ADDRESSES:
    logging.info(".env not found, falling back to config.json file...")
    with open('config.json', 'r') as f:
        config = json.load(f)
        TARGET_BT_ADDRESSES = config["TARGET_BT_ADDRESSES"]
        TARGET_AP_MAC_ADDRESSES = config["TARGET_AP_MAC_ADDRESSES"]

# Convert the comma-separated string from .env to a list
if isinstance(TARGET_BT_ADDRESSES, str):
    TARGET_BT_ADDRESSES = TARGET_BT_ADDRESSES.split(',')
if isinstance(TARGET_AP_MAC_ADDRESSES, str):
    TARGET_AP_MAC_ADDRESSES = TARGET_AP_MAC_ADDRESSES.split(',')

# Initialize the camera
camera = picamera.PiCamera()
filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.h264')
camera.start_recording(filename)
recording = True
logging.info("Recording started.")


def update_annotation(camera):
    """Update the annotation text on the camera."""
    camera.annotate_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def is_device_connected_to_bt(bt_addresses):
    """Check if any of the given Bluetooth addresses are visible."""
    for addr in bt_addresses:
        status = bluetooth.lookup_name(addr, timeout=5)
        if status:
            logging.info(f"Device with Bluetooth address {addr} is connected.")
            return True
    return False


def is_in_ap_mode():
    """Check if the device is in AP mode."""
    try:
        output = subprocess.check_output(
            "ip addr show ap0 | grep '192.168.10.1'", shell=True).decode('utf-8').strip()
        return bool(output)
    except Exception:
        return False


def is_device_connected_to_ap(mac_addresses):
    """Check if any of the given MAC addresses are connected to the AP."""
    if not is_in_ap_mode():
        return False

    try:
        # Use the 'iw' command to get a list of connected devices
        output = subprocess.check_output(
            "iw dev ap0 station dump", shell=True).decode('utf-8').strip()

        for mac in mac_addresses:
            if mac in output:
                logging.info(
                    f"Device with MAC address {mac} is connected to AP.")
                return True

        return False
    except Exception as e:
        logging.error(f"Error checking connected devices: {e}")
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
                logging.info("Device detected. Pausing recording.")
                camera.stop_recording()  # Pause recording
                recording = False
        else:
            if not recording:
                logging.info("No devices detected. Resuming recording.")
                camera.start_recording(datetime.now().strftime(
                    '%Y-%m-%d_%H-%M-%S.h264'))  # Resume recording
                recording = True

        logging.info("Waiting for 5 seconds before checking again...")
        time.sleep(5)

except KeyboardInterrupt:
    camera.stop_recording()
    camera.close()
    logging.info("\nRecording stopped.")
