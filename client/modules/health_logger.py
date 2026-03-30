import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

from . import system_helpers

log = logging.getLogger("health")

LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "data", "health_log.json"
)

# Keep 72h of data at 5-minute intervals = 864 entries max
MAX_ENTRIES = 864
INTERVAL_SECONDS = 300  # 5 minutes

_thread = None
_lock = threading.Lock()


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
    """Save entries to the log file."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f)


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
