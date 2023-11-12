import cv2
import websocket
import threading
import time
import datetime

should_send_frames = False
running = True


def send_frames(ws):
    global should_send_frames, running
    cap = cv2.VideoCapture(0)

    while running:
        if not should_send_frames:
            time.sleep(0.1)
            continue

        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (1920, 1080))
            retval, buffer = cv2.imencode(
                '.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

            if should_send_frames:
                ws.send(buffer.tobytes(), opcode=websocket.ABNF.OPCODE_BINARY)

        time.sleep(0.05)  # Control frame rate

    cap.release()
    print("Camera released and thread terminating...")


def on_open(ws):
    def run(*args):
        print("WebSocket opened and thread started")
        global running
        ws.send("Python Script")
        send_frames(ws)
        running = False

    threading.Thread(target=run).start()


def on_close(ws, close_status_code, close_msg):
    global running
    print("WebSocket closed")
    running = False


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
        running = False
