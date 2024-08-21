import cv2
from flask import Flask, Response, jsonify
from flask_cors import CORS
import os
import threading
from datetime import datetime
import system_helpers

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


@app.route('/system_info', methods=['GET'])
def system_info():
    cpu_temp = system_helpers.get_cpu_temp()
    cpu_load = system_helpers.get_cpu_load()
    storage_info = system_helpers.get_storage_info()
    ram_usage = system_helpers.get_ram_usage()

    return jsonify({
        "cpu_temp_celsius": cpu_temp,
        "cpu_load_percent": cpu_load,
        "storage_info_gb": storage_info,
        "ram_usage_mb": ram_usage
    })


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


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
    app.run(host='0.0.0.0', port=5000, debug=True)
