import cv2
from flask import Flask, render_template, Response, request, jsonify
import threading
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create a lock for thread-safe access to the recording flag and writer
lock = threading.Lock()
out = None
is_recording = False

os.makedirs('./recordings', exist_ok=True)


def generate_frames():
    global out, is_recording
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        with lock:
            if is_recording and out is not None:
                out.write(frame)

        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Use yield to return the frame as a byte array
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def start_recording():
    global out, is_recording
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'./recordings/output_{timestamp}.avi'

    # Set up the video writer
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    with lock:
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        is_recording = True


def stop_recording():
    global out, is_recording
    with lock:
        if out is not None:
            out.release()
            out = None
        is_recording = False


@app.route('/toggle_recording', methods=['POST'])
def toggle_recording():
    global is_recording
    if is_recording:
        stop_recording()
        return jsonify({"message": "Recording stopped"})
    else:
        start_recording()
        return jsonify({"message": "Recording started"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
