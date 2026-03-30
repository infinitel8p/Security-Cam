from flask import Flask, jsonify, send_file, request, abort
from flask_cors import CORS
from urllib.parse import unquote
from modules import system_helpers
from modules import stream_helpers
from modules import settings_helpers
from modules import archive_helpers
from modules import activity_helpers
from modules import mediamtx_helpers
from modules import health_logger
from modules import event_logger

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

health_logger.start()
event_logger.log_event("system_boot")


@app.route('/system_info', methods=['GET'])
def system_info():
    cpu_temp = system_helpers.get_cpu_temp()
    cpu_load = system_helpers.get_cpu_load()
    storage_info = system_helpers.get_storage_info()
    ram_usage = system_helpers.get_ram_usage()

    uptime = system_helpers.get_uptime()
    throttle = system_helpers.get_throttle_status()

    return jsonify({
        "cpu_temp_celsius": cpu_temp,
        "cpu_load_percent": cpu_load,
        "storage_info_gb": storage_info,
        "ram_usage_mb": ram_usage,
        "uptime_seconds": uptime,
        "throttle": throttle,
    })


@app.route('/recording_status', methods=['GET'])
def recording_status():
    return jsonify({"recording": stream_helpers.is_recording})


@app.route('/toggle_recording', methods=['POST'])
def toggle_recording():
    if stream_helpers.is_recording:
        stream_helpers.stop_recording()
        event_logger.log_event("recording_stopped")
        print("Recording stopped")
        return jsonify({"message": "Recording stopped"})
    else:
        if activity_helpers.is_device_connected_to_bt():
            print("Cannot record while connected to Bluetooth")
            return jsonify({"message": "Cannot record while connected to Bluetooth"}), 400

        stream_helpers.start_recording()
        event_logger.log_event("recording_started")
        print("Recording started")
        return jsonify({"message": "Recording started"})


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return jsonify(settings_helpers.get_settings())
    elif request.method == 'POST':
        new_settings = request.json
        if "VideoSaveLocation" in new_settings:
            success = settings_helpers.update_video_save_location(
                new_settings["VideoSaveLocation"])
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


@app.route('/bt/scan', methods=['POST'])
def bt_scan():
    try:
        devices = activity_helpers.scan_bt_devices()
        return jsonify({"devices": devices})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@app.route('/wifi/stations', methods=['GET'])
def wifi_stations():
    stations = activity_helpers.get_ap_stations()
    ap_mode = activity_helpers.is_in_ap_mode()
    result = {"stations": stations}
    if not ap_mode:
        result["message"] = "Not in AP mode"
    return jsonify(result)


@app.route('/devices/bt/add', methods=['POST'])
def add_bt_device():
    data = request.json
    address = data.get("address", "").strip()
    name = data.get("name", "").strip() or address
    if not address:
        return jsonify({"error": "Address is required"}), 400

    try:
        settings_helpers.pair_bt_device(address)
    except Exception as e:
        return jsonify({"error": f"Pairing failed: {e}"}), 500

    settings = settings_helpers.get_settings()
    bt_list = settings.get("TARGET_BT_ADDRESSES", [])
    if not any(d["address"].lower() == address.lower() for d in bt_list):
        bt_list.append({"address": address, "name": name})
        settings_helpers.update_settings({"TARGET_BT_ADDRESSES": bt_list})

    return jsonify({"message": "Device added"})


@app.route('/devices/bt/remove', methods=['POST'])
def remove_bt_device():
    data = request.json
    address = data.get("address", "").strip()
    if not address:
        return jsonify({"error": "Address is required"}), 400

    try:
        settings_helpers.unpair_bt_device(address)
    except Exception:
        pass  # Best-effort unpair

    settings = settings_helpers.get_settings()
    bt_list = [d for d in settings.get("TARGET_BT_ADDRESSES", [])
               if d["address"].lower() != address.lower()]
    settings_helpers.update_settings({"TARGET_BT_ADDRESSES": bt_list})

    return jsonify({"message": "Device removed"})


@app.route('/devices/wifi/add', methods=['POST'])
def add_wifi_device():
    data = request.json
    address = data.get("address", "").strip()
    name = data.get("name", "").strip() or address
    if not address:
        return jsonify({"error": "Address is required"}), 400

    settings = settings_helpers.get_settings()
    wifi_list = settings.get("TARGET_AP_MAC_ADDRESSES", [])
    if not any(d["address"].lower() == address.lower() for d in wifi_list):
        wifi_list.append({"address": address, "name": name})
        settings_helpers.update_settings({"TARGET_AP_MAC_ADDRESSES": wifi_list})

    return jsonify({"message": "Device added"})


@app.route('/devices/wifi/remove', methods=['POST'])
def remove_wifi_device():
    data = request.json
    address = data.get("address", "").strip()
    if not address:
        return jsonify({"error": "Address is required"}), 400

    settings = settings_helpers.get_settings()
    wifi_list = [d for d in settings.get("TARGET_AP_MAC_ADDRESSES", [])
                 if d["address"].lower() != address.lower()]
    settings_helpers.update_settings({"TARGET_AP_MAC_ADDRESSES": wifi_list})

    return jsonify({"message": "Device removed"})


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

    return send_file(os.path.abspath(video_path), mimetype='video/mp4', conditional=True)


@app.route('/delete_video', methods=['POST'])
def delete_video_route():
    video_path = request.json.get('video_path')
    response, status_code = archive_helpers.delete_video(video_path)
    return jsonify(response), status_code


@app.route('/stream_settings', methods=['GET', 'POST'])
def stream_settings():
    if request.method == 'GET':
        try:
            params = mediamtx_helpers.read_config()
            return jsonify(params)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    data = request.json or {}
    params = {}

    for key in ('width', 'height', 'fps'):
        if key in data:
            params[key] = data[key]

    # If rotation is in stream mode, apply it to MediaMTX
    if 'rotation_angle' in data:
        params['rotation_angle'] = data['rotation_angle']

    if not params:
        return jsonify({"message": "No parameters provided"}), 400

    success, error = mediamtx_helpers.update_stream_params(params)
    if success:
        return jsonify({"message": "Stream settings updated, MediaMTX restarted"})
    else:
        return jsonify({"message": error}), 400


@app.route('/health_history', methods=['GET'])
def health_history():
    hours = request.args.get('hours', 24, type=int)
    hours = min(hours, 72)
    return jsonify(health_logger.get_history(hours))


@app.route('/event_history', methods=['GET'])
def event_history():
    hours = request.args.get('hours', 168, type=int)
    hours = min(hours, 168)
    return jsonify(event_logger.get_events(hours))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005, debug=True)
