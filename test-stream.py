import cv2
import websocket
import _thread
import time


def on_open(ws):
    def run(*args):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if ret:
                # Convert the image to JPEG
                retval, buffer = cv2.imencode(
                    '.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])

                # Send the binary data
                ws.send(buffer.tobytes(), opcode=websocket.ABNF.OPCODE_BINARY)

            # Sleep for a bit to prevent overwhelming the server
            time.sleep(0.1)

        cap.release()
        ws.close()
        print("Thread terminating...")

    _thread.start_new_thread(run, ())


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:3000", on_open=on_open)
    ws.run_forever()
