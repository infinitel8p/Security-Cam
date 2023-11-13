import io
import json
import logging
import os
import time
from datetime import datetime

import RPi.GPIO as GPIO
import picamera
from dotenv import load_dotenv
import websocket
import threading

from functions import *


# Set up logging with custom timestamp format
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
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
camera.annotate_background = picamera.Color('black')
jpeg_quality = 85
stream = io.BytesIO()
recording = False
streaming = True
should_send_frames = False

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
Digital_Pin = 22
GPIO.setup(Digital_Pin, GPIO.IN)


def send_frames(ws):
    global should_send_frames, streaming

    while streaming:
        if not should_send_frames:
            time.sleep(0.1)
            continue

        if recording:
            print("Recording in progress, skipping frame...")

        camera.capture(stream, format='jpeg',
                       use_video_port=True, quality=jpeg_quality)
        if should_send_frames:
            stream.seek(0)
            buffer = stream.read()
            ws.send(buffer, opcode=websocket.ABNF.OPCODE_BINARY)

        stream.seek(0)
        stream.truncate()

    camera.close()
    logging.info("Camera released and thread terminating...")


def on_open(ws):
    def run(*args):
        logging.info("WebSocket opened and thread started")
        global streaming
        ws.send("Python Script")
        send_frames(ws)
        streaming = False

    threading.Thread(target=run, name="WebSocketStreamThread").start()


def on_close(ws, close_status_code, close_msg):
    global streaming
    logging.info("WebSocket closed")
    streaming = False


def on_message(ws, message):
    global should_send_frames
    if message == "START":
        logging.info("Streaming requested, sending frames...")
        should_send_frames = True
    elif message == "STOP":
        logging.info("Streaming stopped, no longer sending frames...")
        should_send_frames = False


def start_websocket():
    ws = websocket.WebSocketApp(
        "ws://localhost:3000",
        on_open=on_open,
        on_message=on_message,
        on_close=on_close
    )
    ws.run_forever()


try:
    threading.Thread(target=start_websocket,
                     name="WebSocketSetupThread", daemon=True).start()

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
                        f"./server/public/recordings/video_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.h264")
                    recording = True
        time.sleep(1)
except KeyboardInterrupt:
    streaming = False
    if recording:
        camera.stop_recording()
    camera.close()
    logging.info(
        "Script interrupted by user (Ctrl+C! Recording stopped. Exiting...")
finally:
    GPIO.cleanup()
