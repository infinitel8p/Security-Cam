from picamera import PiCamera
import io
import websocket
import threading
import time
import datetime

streaming = True
should_send_frames = False


def send_frames(ws):
    global should_send_frames, streaming
    camera = PiCamera()
    jpeg_quality = 85
    stream = io.BytesIO()

    while streaming:
        if not should_send_frames:
            time.sleep(0.1)
            continue

        camera.capture(stream, format='jpeg',
                       use_video_port=True, quality=jpeg_quality)
        if should_send_frames:
            stream.seek(0)
            buffer = stream.read()
            ws.send(buffer, opcode=websocket.ABNF.OPCODE_BINARY)

        stream.seek(0)
        stream.truncate()

    camera.close()
    print("Camera released and thread terminating...")


def on_open(ws):
    def run(*args):
        print("WebSocket opened and thread started")
        global streaming
        ws.send("Python Script")
        send_frames(ws)
        streaming = False

    threading.Thread(target=run).start()


def on_close(ws, close_status_code, close_msg):
    global streaming
    print("WebSocket closed")
    streaming = False


def on_message(ws, message):
    global should_send_frames
    if message == "START":
        print(datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y") +
              " - Streaming requested, sending frames...")
        should_send_frames = True
    elif message == "STOP":
        print(datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y") +
              " - Streaming stopped, no longer sending frames...")
        should_send_frames = False


if __name__ == "__main__":
    try:
        ws = websocket.WebSocketApp(
            "ws://localhost:3000",
            on_open=on_open,
            on_message=on_message,
            on_close=on_close
        )
        ws.run_forever()
    except KeyboardInterrupt:
        print("Script interrupted by user (Ctrl+C). Exiting...")
        streaming = False