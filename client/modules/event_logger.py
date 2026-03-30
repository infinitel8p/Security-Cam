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
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "severity": severity,
    }
    if detail:
        entry["detail"] = detail

    log.info("Event: %s [%s]%s", event_type, severity, f" — {detail}" if detail else "")

    with _lock:
        entries = _load_log()
        entries.append(entry)
        if len(entries) > MAX_ENTRIES:
            entries = entries[-MAX_ENTRIES:]
        _save_log(entries)


def get_events(hours=24):
    """Get events for the last N hours."""
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
