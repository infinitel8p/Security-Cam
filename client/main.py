import logging
from logging.handlers import RotatingFileHandler
import os
import subprocess
from flask import Flask, jsonify, send_file, request, abort, Response
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
from modules import presence_monitor
from modules import sensor_manager
from modules import storage_manager
from modules import sse
from modules.sensors import available_types as sensor_available_types

# --- Logging setup ---
LOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "security-cam.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        ),
        logging.StreamHandler(),
    ],
)
# Quiet noisy libraries
logging.getLogger("werkzeug").setLevel(logging.WARNING)

log = logging.getLogger("api")
bt_log = logging.getLogger("bt.api")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.before_request
def log_request():
    log.info("%s %s (from %s)", request.method, request.path, request.remote_addr)


@app.after_request
def log_response(response):
    if response.status_code >= 400:
        log.warning("%s %s → %s", request.method, request.path, response.status)
    return response


@app.route('/events', methods=['GET'])
def events():
    """Server-Sent Events endpoint for real-time state updates."""
    return Response(sse.stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache',
                             'X-Accel-Buffering': 'no'})


health_logger.start()
presence_monitor.start()
sensor_manager.start()
storage_manager.start()

def _on_ffmpeg_crash():
    sensor_manager.notify_manual_recording_stopped()
    event_logger.log_event("recording_stopped", "ffmpeg crash")
    log.warning("FFmpeg crashed - recording state reset")

stream_helpers.set_on_crash(_on_ffmpeg_crash)

event_logger.log_event("system_boot")
log.info("Security Cam backend started")


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
        sensor_manager.notify_manual_recording_stopped()
        event_logger.log_event("recording_stopped")
        sse.emit("recording_state", {"recording": False})
        log.info("Recording stopped (manual)")
        return jsonify({"message": "Recording stopped"})
    else:
        # Manual recording is always allowed - presence gating only
        # applies to automatic sensor-triggered recording (sensor_manager).
        stream_helpers.start_recording()
        event_logger.log_event("recording_started")
        sse.emit("recording_state", {"recording": True})
        log.info("Recording started (manual)")
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
            log.error("Error listing directories: %s", error)
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


@app.route('/devices/status', methods=['GET'])
def device_status():
    return jsonify(activity_helpers.get_device_statuses())


@app.route('/connections', methods=['GET'])
def connections():
    statuses = activity_helpers.get_device_statuses()
    bt_online = sum(1 for v in statuses["bt"].values() if v)
    bt_total = len(statuses["bt"])
    wifi_online = sum(1 for v in statuses["wifi"].values() if v)
    wifi_total = len(statuses["wifi"])

    # Total AP clients (not just tracked ones)
    ap_clients = len(activity_helpers.get_ap_stations()) if activity_helpers.is_in_ap_mode() else 0

    return jsonify({
        "bluetooth": {"online": bt_online, "total": bt_total},
        "wifi": {"online": wifi_online, "total": wifi_total},
        "ap_clients": ap_clients,
    })


@app.route('/bt/discoverable', methods=['POST'])
def bt_discoverable():
    """Make the Pi discoverable for incoming Bluetooth pairing."""
    timeout = request.json.get("timeout", 90) if request.json else 90
    try:
        device = settings_helpers.make_bt_discoverable(timeout=timeout)
        # Auto-register the paired device
        settings = settings_helpers.get_settings()
        bt_list = settings.get("TARGET_BT_ADDRESSES", [])
        addr = device["address"]
        if not any(d["address"].lower() == addr.lower() for d in bt_list):
            bt_list.append(device)
            settings_helpers.update_settings({"TARGET_BT_ADDRESSES": bt_list})
        bt_log.info("Discoverable: device registered: %s (%s)", device["name"], addr)
        return jsonify({"device": device})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 408  # Request Timeout
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Discoverable mode timed out"}), 408
    except Exception as e:
        bt_log.error("Discoverable failed: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route('/devices/bt/add', methods=['POST'])
def add_bt_device():
    data = request.json
    address = (data.get("address") or "").strip()
    name = (data.get("name") or "").strip() or address
    if not address:
        return jsonify({"error": "Address is required"}), 400

    try:
        settings_helpers.pair_bt_device(address)
    except Exception as e:
        bt_log.error("Add failed for %s: %s", address, e)
        return jsonify({"error": f"Pairing failed: {e}"}), 500

    settings = settings_helpers.get_settings()
    bt_list = settings.get("TARGET_BT_ADDRESSES", [])
    if not any(d["address"].lower() == address.lower() for d in bt_list):
        bt_list.append({"address": address, "name": name})
        settings_helpers.update_settings({"TARGET_BT_ADDRESSES": bt_list})

    bt_log.info("Device added: %s (%s)", name, address)
    return jsonify({"message": "Device added"})


@app.route('/devices/bt/remove', methods=['POST'])
def remove_bt_device():
    data = request.json
    address = (data.get("address") or "").strip()
    if not address:
        return jsonify({"error": "Address is required"}), 400

    try:
        settings_helpers.unpair_bt_device(address)
    except Exception as e:
        bt_log.warning("Unpair best-effort failed for %s: %s", address, e)

    settings = settings_helpers.get_settings()
    bt_list = [d for d in settings.get("TARGET_BT_ADDRESSES", [])
               if d["address"].lower() != address.lower()]
    settings_helpers.update_settings({"TARGET_BT_ADDRESSES": bt_list})

    bt_log.info("Device removed: %s", address)
    return jsonify({"message": "Device removed"})


@app.route('/devices/wifi/add', methods=['POST'])
def add_wifi_device():
    data = request.json
    address = (data.get("address") or "").strip()
    name = (data.get("name") or "").strip() or address
    if not address:
        return jsonify({"error": "Address is required"}), 400

    settings = settings_helpers.get_settings()
    wifi_list = settings.get("TARGET_AP_MAC_ADDRESSES", [])
    if not any(d["address"].lower() == address.lower() for d in wifi_list):
        wifi_list.append({"address": address, "name": name})
        settings_helpers.update_settings({"TARGET_AP_MAC_ADDRESSES": wifi_list})

    log.info("WiFi device added: %s (%s)", name, address)
    return jsonify({"message": "Device added"})


@app.route('/devices/wifi/remove', methods=['POST'])
def remove_wifi_device():
    data = request.json
    address = (data.get("address") or "").strip()
    if not address:
        return jsonify({"error": "Address is required"}), 400

    settings = settings_helpers.get_settings()
    wifi_list = [d for d in settings.get("TARGET_AP_MAC_ADDRESSES", [])
                 if d["address"].lower() != address.lower()]
    settings_helpers.update_settings({"TARGET_AP_MAC_ADDRESSES": wifi_list})

    log.info("WiFi device removed: %s", address)
    return jsonify({"message": "Device removed"})


# --- Storage management endpoints ---


@app.route('/storage/status', methods=['GET'])
def storage_status():
    return jsonify(storage_manager.get_status())


@app.route('/storage/configure', methods=['POST'])
def storage_configure():
    data = request.json or {}
    enabled = data.get("enabled")
    max_percent = data.get("max_percent")

    settings = settings_helpers.get_settings()
    cfg = settings.get("StorageLimit", {"enabled": False, "max_percent": 85})

    if enabled is not None:
        cfg["enabled"] = bool(enabled)
    if max_percent is not None:
        cfg["max_percent"] = max(10, min(95, int(max_percent)))

    settings_helpers.update_settings({"StorageLimit": cfg})
    log.info("Storage limit configured: %s", cfg)
    return jsonify({"message": "Storage limit configured", "config": cfg})


@app.route('/storage/cleanup', methods=['POST'])
def storage_cleanup():
    """Manually trigger a storage cleanup."""
    result = storage_manager.check_and_cleanup()
    return jsonify(result)


# --- Sensor endpoints ---


@app.route('/sensor/status', methods=['GET'])
def sensor_status():
    return jsonify(sensor_manager.get_status())


@app.route('/sensor/types', methods=['GET'])
def sensor_types():
    return jsonify(sensor_available_types())


@app.route('/sensor/configure', methods=['POST'])
def sensor_configure():
    data = request.json or {}
    sensor_type = data.get("type")
    if not sensor_type:
        return jsonify({"error": "sensor type is required"}), 400

    from modules.sensors import SENSOR_REGISTRY
    if sensor_type not in SENSOR_REGISTRY:
        return jsonify({"error": f"Unknown sensor type: {sensor_type}",
                        "available": list(SENSOR_REGISTRY.keys())}), 400

    gpio = data.get("gpio")
    enabled = data.get("enabled", True)
    hold_seconds = data.get("hold_seconds", 10)
    invert_logic = data.get("invert_logic", False)
    calibration = data.get("calibration")

    cfg = sensor_manager.configure(sensor_type, gpio=gpio,
                                   enabled=enabled, hold_seconds=hold_seconds,
                                   invert_logic=invert_logic,
                                   calibration=calibration)
    log.info("Sensor configured: %s", cfg)
    return jsonify({"message": "Sensor configured", "config": cfg})


@app.route('/sensor/enable', methods=['POST'])
def sensor_enable():
    settings = settings_helpers.get_settings()
    sensor_cfg = settings.get("Sensor", {})
    sensor_cfg["enabled"] = True
    settings_helpers.update_settings({"Sensor": sensor_cfg})
    sensor_manager.restart()
    log.info("Sensor enabled")
    return jsonify({"message": "Sensor enabled"})


@app.route('/sensor/disable', methods=['POST'])
def sensor_disable():
    sensor_manager.stop()
    settings = settings_helpers.get_settings()
    sensor_cfg = settings.get("Sensor", {})
    sensor_cfg["enabled"] = False
    settings_helpers.update_settings({"Sensor": sensor_cfg})
    log.info("Sensor disabled")
    return jsonify({"message": "Sensor disabled"})


@app.route('/sensor/mock/trigger', methods=['POST'])
def sensor_mock_trigger():
    """Simulate a trigger event (only works when mock sensor is active)."""
    sensor = sensor_manager.get_active_sensor()
    if sensor is None or sensor.sensor_type != "mock":
        return jsonify({"error": "Mock sensor is not active"}), 400
    sensor.trigger()
    return jsonify({"message": "Mock trigger fired"})


@app.route('/sensor/mock/release', methods=['POST'])
def sensor_mock_release():
    """Simulate a release event (only works when mock sensor is active)."""
    sensor = sensor_manager.get_active_sensor()
    if sensor is None or sensor.sensor_type != "mock":
        return jsonify({"error": "Mock sensor is not active"}), 400
    sensor.release()
    return jsonify({"message": "Mock release fired"})


@app.route('/sensor/test', methods=['POST'])
def sensor_test():
    """Read the raw GPIO pin value for wiring verification.

    Accepts {"type": "reed_switch", "gpio": 22} - creates a temporary
    sensor instance, reads the pin, and returns the value.  Does not
    interfere with the running sensor manager.
    """
    data = request.json or {}
    sensor_type = data.get("type")
    gpio = data.get("gpio")

    if not sensor_type:
        return jsonify({"error": "sensor type is required"}), 400

    from modules.sensors import SENSOR_REGISTRY
    if sensor_type not in SENSOR_REGISTRY:
        return jsonify({"error": f"Unknown sensor type: {sensor_type}"}), 400

    if sensor_type == "mock":
        return jsonify({"value": None, "message": "Mock sensor has no GPIO to test"})

    # If the requested sensor is already running with the same GPIO, read from it
    active = sensor_manager.get_active_sensor()
    if active and active.sensor_type == sensor_type and active.gpio == gpio:
        val = active.read_value()
        return jsonify({"value": val, "gpio": gpio, "type": sensor_type})

    # Otherwise create a temporary instance just to read the pin
    from modules.sensors import create_sensor
    try:
        tmp = create_sensor(sensor_type, gpio=gpio)
        val = tmp.read_value()
        return jsonify({"value": val, "gpio": gpio, "type": sensor_type})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    hours = min(hours, 4380)  # ~6 months max
    return jsonify(event_logger.get_events(hours))


if __name__ == "__main__":
    # use_reloader=False: the Werkzeug reloader spawns a parent + child
    # process.  Both run module-level code, so the parent grabs the GPIO
    # pin first and the child (which serves HTTP) can never arm the sensor.
    # Disabling the reloader keeps a single process that owns both the
    # GPIO and the HTTP server.
    app.run(host='0.0.0.0', port=5005, debug=False, use_reloader=False)
