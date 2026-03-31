"""Storage manager - auto-delete oldest recordings when disk is full.

Checks disk usage against a configurable threshold and removes the
oldest recordings (by modification time) until usage drops below the
limit.  Called automatically before each recording starts and
periodically in the background.
"""

import logging
import os
import threading
import time

import psutil

from . import settings_helpers

log = logging.getLogger("storage_mgr")

_CHECK_INTERVAL = 300  # seconds between background checks (5 min)
_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _get_config() -> tuple[bool, int]:
    """Return (enabled, max_percent) from settings."""
    settings = settings_helpers.get_settings()
    cfg = settings.get("StorageLimit", {})
    enabled = cfg.get("enabled", False)
    max_percent = cfg.get("max_percent", 85)
    return enabled, max(10, min(95, max_percent))


def _get_recordings_oldest_first() -> list[str]:
    """Return list of .mp4 recording paths sorted oldest first."""
    settings = settings_helpers.get_settings()
    video_dir = settings.get("VideoSaveLocation", "./recordings")
    if not os.path.isdir(video_dir):
        return []

    files = []
    for root, _dirs, filenames in os.walk(video_dir):
        for f in filenames:
            if f.endswith(".mp4") and not f.endswith(".tmp.mp4"):
                path = os.path.join(root, f)
                files.append(path)

    files.sort(key=lambda p: os.path.getmtime(p))
    return files


def _delete_recording(path: str) -> int:
    """Delete a recording and its sidecar metadata. Returns bytes freed."""
    freed = 0
    try:
        freed += os.path.getsize(path)
        os.remove(path)
        # Remove sidecar metadata
        meta_path = os.path.splitext(path)[0] + ".meta.json"
        if os.path.exists(meta_path):
            freed += os.path.getsize(meta_path)
            os.remove(meta_path)
        log.info("Auto-deleted oldest recording: %s (freed %d MB)",
                 os.path.basename(path), freed // (1024 * 1024))
    except Exception as e:
        log.error("Failed to auto-delete %s: %s", path, e)
    return freed


def check_and_cleanup() -> dict:
    """Check disk usage and delete oldest recordings if over threshold.

    Returns a summary dict with what happened.
    """
    enabled, max_percent = _get_config()
    if not enabled:
        return {"enabled": False, "action": "skipped"}

    settings = settings_helpers.get_settings()
    video_dir = settings.get("VideoSaveLocation", "./recordings")

    # Check disk usage of the partition where recordings live
    try:
        usage = psutil.disk_usage(video_dir if os.path.isdir(video_dir) else "/")
    except OSError:
        usage = psutil.disk_usage("/")

    current_percent = usage.percent

    if current_percent <= max_percent:
        return {
            "enabled": True,
            "action": "ok",
            "disk_percent": current_percent,
            "threshold": max_percent,
        }

    log.warning("Disk usage %.1f%% exceeds limit %d%% - cleaning up",
                current_percent, max_percent)

    recordings = _get_recordings_oldest_first()
    deleted_count = 0
    freed_total = 0

    for path in recordings:
        # Re-check after each deletion
        try:
            usage = psutil.disk_usage(video_dir if os.path.isdir(video_dir) else "/")
        except OSError:
            usage = psutil.disk_usage("/")

        if usage.percent <= max_percent:
            break

        freed = _delete_recording(path)
        freed_total += freed
        deleted_count += 1

    log.info("Cleanup complete: deleted %d recording(s), freed %d MB. Disk now at %.1f%%",
             deleted_count, freed_total // (1024 * 1024), usage.percent)

    return {
        "enabled": True,
        "action": "cleaned",
        "deleted": deleted_count,
        "freed_mb": freed_total // (1024 * 1024),
        "disk_percent": usage.percent,
        "threshold": max_percent,
    }


def ensure_storage():
    """Quick check before recording starts. Non-blocking if disabled."""
    enabled, _ = _get_config()
    if enabled:
        check_and_cleanup()


def get_status() -> dict:
    """Return current storage status for the API."""
    enabled, max_percent = _get_config()
    settings = settings_helpers.get_settings()
    video_dir = settings.get("VideoSaveLocation", "./recordings")

    try:
        usage = psutil.disk_usage(video_dir if os.path.isdir(video_dir) else "/")
    except OSError:
        usage = psutil.disk_usage("/")

    return {
        "enabled": enabled,
        "max_percent": max_percent,
        "disk_percent": round(usage.percent, 1),
        "disk_total_gb": round(usage.total / (1024 ** 3), 1),
        "disk_used_gb": round(usage.used / (1024 ** 3), 1),
        "disk_free_gb": round(usage.free / (1024 ** 3), 1),
    }


# --- Background thread ---

def _background_loop():
    """Periodically check disk usage and clean up if needed."""
    while not _stop_event.is_set():
        try:
            check_and_cleanup()
        except Exception as e:
            log.error("Background storage check failed: %s", e)
        _stop_event.wait(_CHECK_INTERVAL)


def start():
    """Start the background storage monitor."""
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_background_loop, daemon=True,
                               name="storage-monitor")
    _thread.start()
    log.info("Storage monitor started (check every %ds)", _CHECK_INTERVAL)


def stop():
    """Stop the background storage monitor."""
    global _thread
    _stop_event.set()
    if _thread is not None:
        _thread.join(timeout=5)
        _thread = None
    log.info("Storage monitor stopped")
