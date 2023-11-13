import json
import logging
import os
import time
import threading
from datetime import datetime
import picamera
import RPi.GPIO as GPIO
import websocket
from dotenv import load_dotenv
from functions import *

# Set up logging with custom timestamp format
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S')

logging.info("Initializing...")

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

"""
"""

# WebSocket related global variables
should_stream_frames = False
streaming_running = False

# Function to stream frames


def stream_frames():
    global should_stream_frames, streaming_running
    streaming_running = True

    with picamera.PiCamera() as camera:
        camera.resolution = (1920, 1080)
        camera.framerate = 24
        stream = io.BytesIO()

        for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
            if not should_stream_frames:
                break

            # Send frame
            stream.seek(0)
            buffer = stream.read()
            if should_stream_frames:
                ws.send(buffer, opcode=websocket.ABNF.OPCODE_BINARY)

            stream.seek(0)
            stream.truncate()

    streaming_running = False

# WebSocket handlers


def on_open(ws):
    print("WebSocket opened and thread started")
    global streaming_running
    if not streaming_running:
        threading.Thread(target=stream_frames).start()


def on_close(ws, close_status_code, close_msg):
    global should_stream_frames
    print("WebSocket closed")
    ws.send("Python Script")
    should_stream_frames = False


def on_message(ws, message):
    global should_stream_frames
    if message == "START":
        should_stream_frames = True
    elif message == "STOP":
        should_stream_frames = False


# Initialize WebSocket
ws = websocket.WebSocketApp(
    "ws://localhost:3000",
    on_open=on_open,
    on_message=on_message,
    on_close=on_close
)

# Run WebSocket in a separate thread
threading.Thread(target=ws.run_forever).start()

try:
    while True:
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
                        f"./server/public/recordings/video_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.h264")
                    recording = True
        time.sleep(1)
except KeyboardInterrupt:
    if recording:
        camera.stop_recording()
    camera.close()
    logging.info("Script manually interrupted! Recording stopped.")
finally:
    if streaming_running:
        should_stream_frames = False
    GPIO.cleanup()
