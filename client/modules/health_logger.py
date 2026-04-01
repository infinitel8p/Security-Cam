import json
import logging
import os
import tempfile
import threading
import time
from datetime import datetime, timezone

import psutil

from . import system_helpers
from . import sse

log = logging.getLogger("system.health")

LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "data", "health_log.json"
)

# Keep 72h of data at 5-minute intervals = 864 entries max
MAX_ENTRIES = 864
INTERVAL_SECONDS = 300  # 5 minutes

_thread = None
_lock = threading.Lock()

# Alert state tracking — only emit SSE on transitions
_prev_alerts: dict[str, str] = {}
_current_alert_state: dict = {"overall": "ok", "alerts": {}, "values": {}}


def _classify(info):
    """Classify a health snapshot into a status: ok, warn, critical, or unknown."""
    if info is None:
        return "unknown"

    temp = info.get("cpu_temp")
    load = info.get("cpu_load")
    throttle = info.get("throttle_active")

    if throttle or (temp is not None and temp >= 80):
        return "critical"
    if (temp is not None and temp >= 65) or (load is not None and load >= 90):
        return "warn"
    return "ok"


def _snapshot():
    """Take a single health snapshot."""
    temp = system_helpers.get_cpu_temp()
    load = system_helpers.get_cpu_load()
    throttle = system_helpers.get_throttle_status()

    throttle_active = False
    if throttle:
        throttle_active = (
            throttle["under_voltage_now"] or
            throttle["throttled_now"] or
            throttle["freq_capped_now"] or
            throttle["soft_temp_limit_now"]
        )

    info = {
        "cpu_temp": temp,
        "cpu_load": load,
        "throttle_active": throttle_active,
    }

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": _classify(info),
        "temp": temp,
        "load": load,
        "throttle_active": throttle_active,
    }


def _load_log():
    """Load the log file, return list of entries."""
    if not os.path.exists(LOG_PATH):
        return []
    try:
        with open(LOG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_log(entries):
    """Save entries to the log file atomically."""
    dirpath = os.path.dirname(LOG_PATH)
    os.makedirs(dirpath, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(entries, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, LOG_PATH)
    except BaseException:
        os.unlink(tmp)
        raise


def evaluate_alerts(info: dict) -> dict[str, str]:
    """Evaluate per-metric alert levels from a snapshot dict.

    Args:
        info: dict with keys temp, load, throttle_active, and optionally
              storage_pct and sd_life_est.

    Returns:
        dict mapping metric names to "ok", "warn", or "critical".
    """
    alerts: dict[str, str] = {}

    # CPU temperature
    temp = info.get("temp") or info.get("cpu_temp")
    if temp is not None:
        if temp >= 80:
            alerts["cpu_temp"] = "critical"
        elif temp >= 65:
            alerts["cpu_temp"] = "warn"
        else:
            alerts["cpu_temp"] = "ok"

    # Throttling
    if info.get("throttle_active"):
        alerts["throttle"] = "critical"
    else:
        alerts["throttle"] = "ok"

    # Storage
    storage_pct = info.get("storage_pct")
    if storage_pct is None:
        try:
            storage_pct = round(psutil.disk_usage("/").percent, 1)
        except Exception:
            storage_pct = None
    if storage_pct is not None:
        if storage_pct >= 95:
            alerts["storage"] = "critical"
        elif storage_pct >= 85:
            alerts["storage"] = "warn"
        else:
            alerts["storage"] = "ok"

    # SD card health
    sd_life = info.get("sd_life_est")
    if sd_life is None:
        sd = system_helpers.get_sd_health()
        sd_life = sd.get("life_time_est") if sd else None
    if sd_life is not None:
        try:
            val = int(sd_life, 16) if isinstance(sd_life, str) and sd_life.startswith("0x") else int(sd_life)
            if val >= 0x0B:
                alerts["sd_health"] = "critical"
            elif val >= 0x03:
                alerts["sd_health"] = "warn"
            else:
                alerts["sd_health"] = "ok"
        except (ValueError, TypeError):
            pass

    return alerts


def _check_and_emit_alerts(entry: dict) -> None:
    """Compare current alerts with previous state, emit SSE on transitions."""
    global _prev_alerts, _current_alert_state

    # Build info dict from the snapshot entry
    info = {
        "temp": entry.get("temp"),
        "cpu_temp": entry.get("temp"),
        "load": entry.get("load"),
        "throttle_active": entry.get("throttle_active", False),
    }
    alerts = evaluate_alerts(info)

    # Compute overall level
    levels = list(alerts.values())
    if "critical" in levels:
        overall = "critical"
    elif "warn" in levels:
        overall = "warn"
    else:
        overall = "ok"

    # Collect current values for toast messages
    values = {"temp": entry.get("temp"), "load": entry.get("load")}
    try:
        values["storage_pct"] = round(psutil.disk_usage("/").percent, 1)
    except Exception:
        pass

    _current_alert_state = {"overall": overall, "alerts": alerts, "values": values}

    # Detect transitions
    transitions = []
    for metric, level in alerts.items():
        prev = _prev_alerts.get(metric, "ok")
        if level != prev:
            transitions.append({"metric": metric, "from": prev, "to": level})

    if transitions:
        sse.emit("system_alert", {
            "overall": overall,
            "alerts": alerts,
            "transitions": transitions,
            "values": values,
            "ts": entry.get("ts"),
        })

    _prev_alerts = dict(alerts)


def get_current_alerts() -> dict:
    """Return the current alert state for the /system_alert_state endpoint."""
    return dict(_current_alert_state)


def _log_loop():
    """Background loop that takes snapshots at regular intervals."""
    while True:
        try:
            entry = _snapshot()
            with _lock:
                entries = _load_log()
                entries.append(entry)
                if len(entries) > MAX_ENTRIES:
                    entries = entries[-MAX_ENTRIES:]
                _save_log(entries)
            _check_and_emit_alerts(entry)
        except Exception as e:
            log.error("Health logger error: %s", e)
        time.sleep(INTERVAL_SECONDS)


def start():
    """Start the background health logger thread."""
    global _thread
    if _thread is not None:
        return
    _thread = threading.Thread(target=_log_loop, daemon=True)
    _thread.start()
    log.info("Health logger started (5-minute intervals)")


def get_history(hours=24):
    """Get health history for the last N hours."""
    with _lock:
        entries = _load_log()
    if not entries:
        return []

    cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
    result = []
    for entry in entries:
        try:
            ts = datetime.fromisoformat(entry["ts"]).timestamp()
            if ts >= cutoff:
                result.append(entry)
        except (ValueError, KeyError):
            continue
    return result
