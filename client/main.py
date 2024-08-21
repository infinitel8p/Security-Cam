from flask import Flask, jsonify, send_file, Response, request, abort
from flask_cors import CORS
from urllib.parse import unquote
from modules import system_helpers
from modules import stream_helpers
from modules import settings_helpers
from modules import archive_helpers

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
    

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return jsonify(settings_helpers.get_settings())
    elif request.method == 'POST':
        new_settings = request.json
        if "VideoSaveLocation" in new_settings:
            success = settings_helpers.update_video_save_location(new_settings["VideoSaveLocation"])
            if success:
                return jsonify({"message": "Settings updated"})
            else:
                return jsonify({"message": "Invalid directory or insufficient permissions"}), 400
        else:
            settings_helpers.update_settings(new_settings)
            return jsonify({"message": "Settings updated"})


@app.route('/list_directories', methods=['GET'])
def list_directories():
    path = request.args.get('path', "./")
    decoded_path = unquote(path)  # Decode the path

    if settings_helpers.is_directory(decoded_path):
        directories, error = settings_helpers.list_directories(decoded_path)
        if error:
            print(f"Error listing directories: {error}")
            return jsonify({"error": error}), 500
        return jsonify(directories)
    else:
        return jsonify({"error": "Invalid directory path"}), 400
    
@app.route('/archive', methods=['GET'])
def archive():
    video_list = archive_helpers.get_videos()
    return jsonify(video_list)

@app.route('/stream_video', methods=['GET'])
def stream_video():
    import os
    video_path = request.args.get('video_path')
    
    if not video_path or not os.path.exists(video_path):
        abort(404, description="Video not found")

    return send_file(video_path, as_attachment=True, download_name=os.path.basename(video_path), mimetype='video/mp4')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005, debug=True)
