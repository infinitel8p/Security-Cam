from flask import Flask, Response, jsonify
from flask_cors import CORS
import system_helpers
import stream_helpers

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


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
    return Response(stream_helpers.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/toggle_recording', methods=['POST'])
def toggle_recording():
    global is_recording
    if stream_helpers.is_recording:
        stream_helpers.stop_recording()
        return jsonify({"message": "Recording stopped"})
    else:
        stream_helpers.start_recording()
        return jsonify({"message": "Recording started"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005, debug=True)
