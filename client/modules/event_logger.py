import json
import logging
import os
import threading
from datetime import datetime, timezone

log = logging.getLogger("events")

LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "data", "event_log.json"
)

MAX_ENTRIES = 5000
MIN_DUPLICATE_INTERVAL = 120  # seconds - suppress identical events within this window
_lock = threading.Lock()

# Event types and their severity for the tracker
# ok: normal/expected events
# warn: notable but not alarming
# critical: needs attention
EVENT_TYPES = {
    "device_arrived": "ok",
    "device_left": "ok",
    "recording_started": "warn",
    "recording_stopped": "ok",
    "motion_detected": "warn",
    "sensor_triggered": "warn",
    "sensor_released": "ok",
    "sensor_armed": "ok",
    "sensor_disarmed": "ok",
    "stream_disconnected": "critical",
    "stream_reconnected": "ok",
    "unauthorized_access": "critical",
    "system_boot": "ok",
}


def _load_log():
    if not os.path.exists(LOG_PATH):
        return []
    try:
        with open(LOG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_log(entries):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f)


def log_event(event_type, detail=None):
    """Log a security/activity event.

    Args:
        event_type: One of EVENT_TYPES keys.
        detail: Optional string with extra context (e.g. device name).
    """
    severity = EVENT_TYPES.get(event_type, "ok")
    now = datetime.now(timezone.utc)
    entry = {
        "ts": now.isoformat(),
        "type": event_type,
        "severity": severity,
    }
    if detail:
        entry["detail"] = detail

    with _lock:
        entries = _load_log()

        # Suppress duplicate: same type+detail within MIN_DUPLICATE_INTERVAL
        if entries:
            last = entries[-1]
            if last["type"] == event_type and last.get("detail") == detail:
                try:
                    last_ts = datetime.fromisoformat(last["ts"]).timestamp()
                    if now.timestamp() - last_ts < MIN_DUPLICATE_INTERVAL:
                        log.debug("Suppressed duplicate event: %s", event_type)
                        return
                except (ValueError, KeyError):
                    pass

        log.info("Event: %s [%s]%s", event_type, severity, f" - {detail}" if detail else "")
        entries.append(entry)
        if len(entries) > MAX_ENTRIES:
            entries = entries[-MAX_ENTRIES:]
        _save_log(entries)


def get_events(hours=24):
    """Get events for the last N hours."""
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
