import os
import cv2
import threading
from datetime import datetime

# Lock for thread-safe access to the recording flag and writer
lock = threading.Lock()
out = None
is_recording = False

# Ensure recordings directory exists
os.makedirs('./recordings', exist_ok=True)


def generate_frames():
    """
    Captures frames from the default camera feed, encodes them as JPEG images, and yields them as byte streams.

    Yields:
        bytes: A sequence of JPEG-encoded image frames as byte streams, suitable for streaming in an HTTP response.

    Returns:
        None
    """

    global out, is_recording
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        with lock:
            if is_recording and out is not None:
                out.write(frame)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


def start_recording() -> None:
    """
    Starts recording video frames from the default camera feed and saves them to a file.

    Returns:
        None
    """

    global out, is_recording
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'./recordings/output_{timestamp}.avi'

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    with lock:
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        is_recording = True


def stop_recording() -> None:
    """
    Stops recording video frames and releases the video writer.

    Returns:
        None
    """

    global out, is_recording
    with lock:
        if out is not None:
            out.release()
            out = None
        is_recording = False
