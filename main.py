import json
import logging
import os
import time
from datetime import datetime

import picamera
import RPi.GPIO as GPIO
from dotenv import load_dotenv

from functions import *

logging.info("Initializing...")

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
recording = False

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
Digital_Pin = 22
GPIO.setup(Digital_Pin, GPIO.IN)

# Enable timestamp on the video
camera.annotate_background = picamera.Color('black')

try:
    while True:
        update_annotation(camera)
        if GPIO.input(Digital_Pin):
            logging.info("Door is closed.")

            if recording:
                logging.info("Recording was in progress. Pausing recording.")
                camera.stop_recording()
                recording = False

        else:
            logging.warning("Door is open.")

            # Check if any of the smartphones' Bluetooth addresses are visible or if they're connected to the AP
            if is_device_connected_to_bt(TARGET_BT_ADDRESSES) or is_device_connected_to_ap(TARGET_AP_MAC_ADDRESSES):
                if recording:
                    logging.info("Device detected. Stop recording.")
                    camera.stop_recording()
                    recording = False
            # If no device is connected, start recording
            else:
                if not recording:
                    logging.info("Device not detected. Start recording.")
                    camera.start_recording(
                        f"video_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.h264")
                    recording = True
        time.sleep(1)


except KeyboardInterrupt:
    camera.stop_recording()
    camera.close()
    logging.info("\nScript manually interrupted! Recording stopped.")

finally:
    GPIO.cleanup()
