"""Night vision (IR) detection via pink/magenta hue analysis.

NoIR cameras produce a distinctive pink/magenta color cast under IR
illumination.  This module periodically grabs a frame from the RTSP
stream, converts it to HSV and counts the percentage of pixels whose
hue falls in the magenta range.  When the ratio crosses the configured
threshold the module emits an SSE event so the dashboard can show an
IR badge.
"""

import logging
import threading
import time

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False

from modules import settings_helpers
from modules import sse

log = logging.getLogger("nightvision")

RTSP_URL = "rtsp://localhost:8554/cam"

# Defaults (overridden by settings)
_hue_low = 140
_hue_high = 170
_sat_min = 40
_threshold_pct = 25
_check_interval = 30
_enabled = True

_night_mode = False
_magenta_pct = 0.0
_lock = threading.Lock()
_thread: threading.Thread | None = None


def _load_settings():
    """Read NightVision settings and update module-level config."""
    global _hue_low, _hue_high, _sat_min, _threshold_pct, _check_interval, _enabled
    nv = settings_helpers.get_settings().get("NightVision", {})
    _enabled = nv.get("enabled", True)
    _hue_low = nv.get("hue_low", 140)
    _hue_high = nv.get("hue_high", 170)
    _sat_min = nv.get("saturation_min", 40)
    _threshold_pct = nv.get("threshold_percent", 25)
    _check_interval = nv.get("check_interval_seconds", 30)


def _grab_frame():
    """Grab a single frame from the RTSP stream. Returns BGR ndarray or None."""
    try:
        cap = cv2.VideoCapture(RTSP_URL)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        if not cap.isOpened():
            return None
        ok, frame = cap.read()
        cap.release()
        return frame if ok else None
    except Exception as e:
        log.debug("Frame grab failed: %s", e)
        return None


def _analyze_frame(frame) -> float:
    """Return the percentage of pixels in the magenta hue range."""
    # Downsample for speed
    h, w = frame.shape[:2]
    if w > 320:
        scale = 320 / w
        frame = cv2.resize(frame, (320, int(h * scale)))

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]

    mask = (hue >= _hue_low) & (hue <= _hue_high) & (sat >= _sat_min)
    return float(np.count_nonzero(mask) / mask.size * 100)


def _check_loop():
    """Daemon loop: sample frame, detect magenta, emit SSE on transitions."""
    global _night_mode, _magenta_pct

    while True:
        try:
            _load_settings()

            if not _enabled:
                with _lock:
                    if _night_mode:
                        _night_mode = False
                        _magenta_pct = 0.0
                        sse.emit("night_mode", {"active": False})
                time.sleep(_check_interval)
                continue

            frame = _grab_frame()
            if frame is None:
                time.sleep(_check_interval)
                continue

            pct = _analyze_frame(frame)
            active = pct >= _threshold_pct

            with _lock:
                changed = active != _night_mode
                _night_mode = active
                _magenta_pct = pct

            if changed:
                sse.emit("night_mode", {"active": active})
                log.info("Night mode %s (%.1f%% magenta)",
                         "ON" if active else "OFF", pct)

        except Exception as e:
            log.error("Night vision check error: %s", e)

        time.sleep(_check_interval)


def start():
    """Start the background night-vision detection thread."""
    global _thread
    if _thread is not None:
        return
    if not _HAS_CV2:
        log.warning("OpenCV not available - night vision detection disabled")
        return
    _load_settings()
    _thread = threading.Thread(target=_check_loop, daemon=True)
    _thread.start()
    log.info("Night vision detector started (%ds intervals)", _check_interval)


def is_night_mode() -> bool:
    """Return whether the camera is currently in IR / night mode."""
    with _lock:
        return _night_mode


def get_state() -> dict:
    """Return detailed state for debugging."""
    with _lock:
        return {"active": _night_mode, "magenta_pct": _magenta_pct}
