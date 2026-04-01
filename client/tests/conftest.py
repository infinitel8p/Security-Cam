"""Shared fixtures for all tests.

The Flask app (main.py) starts background threads on import
(health_logger, presence_monitor, sensor_manager, storage_manager).
We mock those out at the module level before importing the app so
the tests can run on any machine without Pi hardware.
"""

import json
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Patch heavy / Pi-dependent modules BEFORE importing the Flask app
# ---------------------------------------------------------------------------

_patches = []


def _start(target, **kwargs):
    p = patch(target, **kwargs)
    _patches.append(p)
    return p.start()


# Background services — prevent threads from spawning
_start("modules.health_logger.start")
_start("modules.health_logger.get_history", return_value=[])
_start("modules.health_logger.get_current_alerts", return_value={
    "overall": "ok", "alerts": {}, "values": {},
})
_start("modules.presence_monitor.start")
_start("modules.sensor_manager.start")
_start("modules.sensor_manager.stop")
_start("modules.sensor_manager.restart")
_start("modules.sensor_manager.get_status", return_value={})
_start("modules.sensor_manager.get_active_sensor", return_value=None)
_start("modules.sensor_manager.configure", return_value={})
_start("modules.sensor_manager.notify_manual_recording_stopped")
_start("modules.storage_manager.start")
_start("modules.storage_manager.stop")
_start("modules.storage_manager.get_status", return_value={
    "disk_percent": 42.0, "disk_total_gb": 16.0,
    "disk_used_gb": 6.7, "disk_free_gb": 9.3,
})
_start("modules.storage_manager.check_and_cleanup", return_value={
    "action": "none", "disk_percent": 42.0,
})
_start("modules.storage_manager.ensure_storage")

# Timelapse — prevent background thread
_start("modules.timelapse_manager.start")
_start("modules.timelapse_manager.stop")
_start("modules.timelapse_manager.restart")
_start("modules.timelapse_manager.get_status", return_value={
    "enabled": False, "interval_minutes": 5, "fps": 24,
    "resolution": "640x480", "today_frame_count": 0, "last_capture": None,
})
_start("modules.timelapse_manager.get_timelapse_videos", return_value=[])

# Stream helpers — no camera / ffmpeg
_start("modules.stream_helpers.set_on_crash")
_start("modules.stream_helpers.start_recording")
_start("modules.stream_helpers.stop_recording")
import modules.stream_helpers as _sh
_sh.is_recording = False

# MediaMTX
_start("modules.mediamtx_helpers.read_config", return_value={
    "width": 1296, "height": 972, "fps": 30,
    "brightness": 0, "contrast": 1, "saturation": 1, "sharpness": 1,
    "ev": 0, "awb": "auto", "exposure": "normal", "denoise": "off",
    "metering": "centre",
})
_start("modules.mediamtx_helpers.update_stream_params",
       return_value=(True, None))
_start("modules.mediamtx_helpers.update_isp_params",
       return_value=(True, None))

# Bluetooth / WiFi (subprocess-heavy)
_start("modules.activity_helpers.scan_bt_devices", return_value=[])
_start("modules.activity_helpers.get_ap_stations", return_value=[])
_start("modules.activity_helpers.is_in_ap_mode", return_value=False)
_start("modules.activity_helpers.get_device_statuses", return_value={
    "bt": {}, "wifi": {},
})
_start("modules.settings_helpers.pair_bt_device", return_value=True)
_start("modules.settings_helpers.unpair_bt_device", return_value=True)

# SSE — prevent real event emission
_start("modules.sse.emit")
_start("modules.sse.stream", return_value=iter([]))

# Event logger — use real logic but patched path (see tmp_data fixture)
_start("modules.event_logger.log_event")

# Now safe to import
from main import app as _flask_app  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app(tmp_path):
    """Yield a configured Flask app with isolated settings / data dirs."""
    # Create a temp settings dir with defaults
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()

    defaults_src = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "settings", "settings.defaults.json",
    )
    shutil.copy(defaults_src, settings_dir / "settings.defaults.json")
    shutil.copy(defaults_src, settings_dir / "settings.json")

    # Create temp recordings dir
    rec_dir = tmp_path / "recordings"
    rec_dir.mkdir()

    # Point settings_helpers at our temp dirs
    import modules.settings_helpers as sh
    orig_sf = sh.SETTINGS_FILE
    orig_df = sh.DEFAULTS_FILE
    sh.SETTINGS_FILE = str(settings_dir / "settings.json")
    sh.DEFAULTS_FILE = str(settings_dir / "settings.defaults.json")

    # Update VideoSaveLocation in temp settings
    with open(sh.SETTINGS_FILE, "r") as f:
        s = json.load(f)
    s["VideoSaveLocation"] = str(rec_dir)
    with open(sh.SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=4)

    _flask_app.config["TESTING"] = True
    yield _flask_app

    # Restore
    sh.SETTINGS_FILE = orig_sf
    sh.DEFAULTS_FILE = orig_df


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def rec_dir(app):
    """Return the temporary recordings directory path."""
    import modules.settings_helpers as sh
    with open(sh.SETTINGS_FILE, "r") as f:
        s = json.load(f)
    return s["VideoSaveLocation"]
