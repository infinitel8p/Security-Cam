"""Sensor manager - connects trigger sensors to recording via presence gating.

Flow:
  sensor trigger → check presence → nobody home? → start recording
  sensor release → (optional hold timeout) → stop recording

The manager is a singleton started from main.py.  It reads the sensor
config from settings, instantiates the right sensor class, and wires
up the callbacks.

Manual recording (/toggle_recording) is never blocked by the sensor
system - this module only controls *automatic* sensor-triggered recording.
"""

import atexit
import logging
import os
import threading
import time

from . import activity_helpers
from . import event_logger
from . import presence_monitor
from . import settings_helpers
from . import stream_helpers
from . import sse
from .sensors import SENSOR_REGISTRY, create_sensor

log = logging.getLogger("sensor.mgr")

_sensor = None
_lock = threading.Lock()
_hold_timer: threading.Timer | None = None

# State exposed to the API
_triggered = False
_armed = False  # True when sensor is running and will auto-record
_sensor_recording = False  # True only when this module started the recording
_suppressed = False  # True when trigger was ignored due to presence

# Rate-limit presence checks for pulse-based sensors (vibration, knock).
# Avoids hammering BT scanning on every rapid pulse.
_last_presence_check_time = 0.0
_last_presence_result = False
_PRESENCE_CHECK_INTERVAL = 5.0  # seconds
_CONFIRM_DELAY = 2.0  # seconds between first and confirmation check


def _emit_state():
    """Push current sensor state to all SSE clients."""
    sse.emit("sensor_state", {
        "enabled": settings_helpers.get_settings().get("Sensor", {}).get("enabled", False),
        "armed": _armed,
        "triggered": _triggered,
        "suppressed": _suppressed,
        "recording_from_sensor": _sensor_recording,
    })


def _check_presence_once() -> tuple[bool, dict]:
    """Run a single presence check. Returns (someone_home, raw_statuses)."""
    settings = settings_helpers.get_settings()
    bt_addrs = settings.get("TARGET_BT_ADDRESSES", [])
    wifi_addrs = settings.get("TARGET_AP_MAC_ADDRESSES", [])

    if not bt_addrs and not wifi_addrs:
        return False, {"bt": {}, "wifi": {}}

    statuses = activity_helpers.get_device_statuses()

    someone_home = (any(statuses["bt"].values())
                    or any(statuses["wifi"].values()))
    return someone_home, statuses


def _report_to_presence_monitor(statuses: dict):
    """Feed BT check results back to the presence monitor for the timeline."""
    for addr, online in statuses["bt"].items():
        presence_monitor.report_bt_status(addr, online)


def _is_someone_home() -> bool:
    """Return True if any tracked device is present (BT or WiFi).

    Uses a rate-limit cache for rapid sensor pulses.
    Results are fed back to the presence monitor for the activity timeline.
    """
    global _last_presence_check_time, _last_presence_result

    now = time.monotonic()
    if now - _last_presence_check_time < _PRESENCE_CHECK_INTERVAL:
        return _last_presence_result

    someone_home, statuses = _check_presence_once()
    _report_to_presence_monitor(statuses)

    _last_presence_check_time = time.monotonic()
    _last_presence_result = someone_home
    return someone_home


def _confirmation_check():
    """Background confirmation: if someone is actually home, roll back the recording.

    Runs after _CONFIRM_DELAY seconds. If the second presence check finds
    a device, stops the recording and deletes the file since it was a
    false alarm caused by a flaky first BT lookup.
    """
    global _sensor_recording, _suppressed

    time.sleep(_CONFIRM_DELAY)

    someone_home, statuses = _check_presence_once()
    _report_to_presence_monitor(statuses)

    if not someone_home:
        log.debug("Presence confirmation: confirmed nobody home, recording continues")
        return

    # False alarm — someone IS home, first check was a flaky BT miss
    log.info("Presence confirmation: device found on second lookup — "
             "rolling back sensor recording (false alarm)")

    with _lock:
        if not _sensor_recording:
            # Recording was already stopped by release/manual/other
            return

        # Grab the filename before stopping
        filename = stream_helpers.recorded_filename

        _sensor_recording = False
        _suppressed = True
        stream_helpers.stop_recording()
        event_logger.log_event("recording_stopped", "presence confirmation (false alarm)")

    _emit_state()
    sse.emit("recording_state", {"recording": False})

    # Delete the short false-alarm recording and its metadata
    if filename:
        for path in [filename,
                     os.path.splitext(filename)[0] + ".meta.json",
                     os.path.splitext(filename)[0] + ".thumb.jpg",
                     os.path.splitext(filename)[0] + ".sprite.jpg"]:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    log.info("Deleted false-alarm file: %s", path)
            except OSError as e:
                log.warning("Could not delete false-alarm file %s: %s", path, e)


def _on_trigger():
    """Called by the active sensor when it fires."""
    global _triggered, _sensor_recording, _suppressed

    with _lock:
        _triggered = True
        _suppressed = False
        _cancel_hold_timer_locked()

        event_logger.log_event("sensor_triggered", _sensor.name if _sensor else None)

        if _sensor_recording:
            # Already recording from a prior trigger - just reset the hold timer
            _emit_state()
            return

    # Presence check runs outside the lock (can be slow / blocking)
    if _is_someone_home():
        log.info("Sensor triggered but device present — skipping recording")
        with _lock:
            _suppressed = True
        _emit_state()
        return

    with _lock:
        if stream_helpers.is_recording:
            log.info("Sensor triggered but already recording (manual)")
            _emit_state()
            return

        log.info("Sensor triggered, no presence detected — starting recording")
        sensor_type = _sensor.sensor_type if _sensor else None
        stream_helpers.start_recording(reason="sensor", sensor_type=sensor_type)
        _sensor_recording = True
        event_logger.log_event("recording_started", "sensor trigger")

    _emit_state()
    sse.emit("recording_state", {"recording": True})

    # Run a background confirmation check — if the first BT lookup was
    # a false negative (device IS home), roll back the recording.
    settings = settings_helpers.get_settings()
    if settings.get("TARGET_BT_ADDRESSES") or settings.get("TARGET_AP_MAC_ADDRESSES"):
        threading.Thread(target=_confirmation_check, daemon=True).start()


def _on_release():
    """Called by the active sensor when it resets."""
    global _triggered, _suppressed

    with _lock:
        _triggered = False
        _suppressed = False
        event_logger.log_event("sensor_released", _sensor.name if _sensor else None)

        if not _sensor_recording:
            _emit_state()
            return

        # Use hold timeout: keep recording for N seconds after release
        # in case of brief interruptions (door bouncing, motion gap)
        settings = settings_helpers.get_settings()
        hold = settings.get("Sensor", {}).get("hold_seconds", 10)

        if hold > 0:
            log.info("Sensor released - holding recording for %ds", hold)
            _start_hold_timer_locked(hold)
        else:
            _stop_sensor_recording_locked()

    _emit_state()


def _stop_sensor_recording_locked():
    """Stop a sensor-initiated recording. Caller must hold _lock."""
    global _sensor_recording
    if not _sensor_recording:
        return
    log.info("Stopping sensor-triggered recording")
    _sensor_recording = False
    stream_helpers.stop_recording()
    event_logger.log_event("recording_stopped", "sensor release")
    sse.emit("recording_state", {"recording": False})


def _start_hold_timer_locked(seconds: float):
    """Start hold timer. Caller must hold _lock."""
    global _hold_timer
    _cancel_hold_timer_locked()
    _hold_timer = threading.Timer(seconds, _hold_expired)
    _hold_timer.daemon = True
    _hold_timer.start()


def _hold_expired():
    global _hold_timer
    with _lock:
        _hold_timer = None
        if not _triggered:
            _stop_sensor_recording_locked()
            _emit_state()
        else:
            log.info("Hold expired but sensor still triggered - continuing recording")


def _cancel_hold_timer_locked():
    """Cancel hold timer. Caller must hold _lock."""
    global _hold_timer
    if _hold_timer is not None:
        _hold_timer.cancel()
        _hold_timer = None


# --- Public API ---


def notify_manual_recording_stopped():
    """Called by /toggle_recording when the user manually stops recording.

    If the sensor manager thinks it owns the current recording, this
    resets that state so a future hold-timer expiry won't accidentally
    stop a later manual recording.
    """
    global _sensor_recording
    with _lock:
        if _sensor_recording:
            log.info("Manual stop overrode sensor recording - resetting sensor state")
            _sensor_recording = False
            _cancel_hold_timer_locked()


def start():
    """Load sensor config from settings and start monitoring if enabled."""
    global _sensor, _armed

    # Clean up any existing sensor to avoid GPIO busy on restart
    if _sensor is not None:
        stop()

    settings = settings_helpers.get_settings()
    sensor_cfg = settings.get("Sensor", {})

    if not sensor_cfg.get("enabled", False):
        log.info("Sensor disabled in settings - skipping start")
        return

    sensor_type = sensor_cfg.get("type", "reed_switch")
    gpio = sensor_cfg.get("gpio")
    invert = sensor_cfg.get("invert_logic", False)
    calibration = sensor_cfg.get("calibration", {})

    if sensor_type not in SENSOR_REGISTRY:
        log.error("Unknown sensor type '%s'", sensor_type)
        return

    try:
        _sensor = create_sensor(sensor_type, gpio=gpio, **calibration)
        if invert:
            # Swap trigger/release so sensor fires on opposite state
            log.info("Trigger logic inverted")
            _sensor.start(on_trigger=_on_release, on_release=_on_trigger)
        else:
            _sensor.start(on_trigger=_on_trigger, on_release=_on_release)
        _armed = True
        event_logger.log_event("sensor_armed", _sensor.name)
        log.info("Sensor manager started: %s (GPIO %s, invert=%s)",
                 _sensor.name, _sensor.gpio, invert)
    except Exception as e:
        log.error("Failed to start sensor '%s': %s", sensor_type, e)
        _armed = False

    _emit_state()


def stop():
    """Stop the active sensor."""
    global _sensor, _armed, _triggered, _sensor_recording, _suppressed

    with _lock:
        _cancel_hold_timer_locked()

        if _sensor is not None:
            name = _sensor.name
            _sensor.stop()
            _sensor = None
            _armed = False
            _triggered = False
            _suppressed = False
            _sensor_recording = False
            event_logger.log_event("sensor_disarmed", name)
            log.info("Sensor manager stopped")

    _emit_state()


atexit.register(lambda: stop())


def restart():
    """Restart with current settings (call after config change)."""
    stop()
    start()


def configure(sensor_type: str, gpio: int | None = None,
              enabled: bool = True, hold_seconds: int = 10,
              invert_logic: bool = False, calibration: dict | None = None):
    """Update sensor settings and restart.

    Returns the new sensor config dict.
    """
    cfg = {
        "type": sensor_type,
        "enabled": enabled,
        "hold_seconds": hold_seconds,
        "invert_logic": invert_logic,
    }
    if gpio is not None:
        cfg["gpio"] = gpio
    else:
        # Use default GPIO for the sensor type
        cls = SENSOR_REGISTRY.get(sensor_type)
        if cls:
            cfg["gpio"] = cls.default_gpio

    if calibration:
        cfg["calibration"] = calibration

    settings_helpers.update_settings({"Sensor": cfg})
    restart()
    return cfg


def get_status() -> dict:
    """Return current sensor status for the API."""
    settings = settings_helpers.get_settings()
    sensor_cfg = settings.get("Sensor", {})

    result = {
        "enabled": sensor_cfg.get("enabled", False),
        "armed": _armed,
        "triggered": _triggered,
        "suppressed": _suppressed,
        "recording_from_sensor": _sensor_recording,
        "hold_seconds": sensor_cfg.get("hold_seconds", 10),
        "config": sensor_cfg,
    }

    if _sensor is not None:
        result["sensor"] = _sensor.describe()
    else:
        result["sensor"] = None

    return result


def get_active_sensor():
    """Return the active sensor instance (or None)."""
    return _sensor
