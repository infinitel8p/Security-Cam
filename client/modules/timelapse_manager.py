"""Daily timelapse generator.

Captures a single JPEG frame from the RTSP stream at a configurable interval
and stitches them into a daily MP4 video when the day rolls over.

Frames are stored in {VideoSaveLocation}/timelapse/{YYYY-MM-DD}/ and the
stitched output goes to {VideoSaveLocation}/timelapse/timelapse_{YYYYMMDD}.mp4.
"""

import glob
import logging
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime

from . import settings_helpers

log = logging.getLogger("timelapse")

RTSP_URL = "rtsp://localhost:8554/cam"

_thread: threading.Thread | None = None
_stop_event = threading.Event()
_last_date: str | None = None
_today_frame_count = 0
_last_capture: str | None = None


def _get_config() -> dict:
    settings = settings_helpers.get_settings()
    return settings.get("Timelapse", {})


def _timelapse_dir() -> str:
    settings = settings_helpers.get_settings()
    video_dir = settings.get("VideoSaveLocation", "./recordings")
    tl_dir = os.path.join(video_dir, "timelapse")
    os.makedirs(tl_dir, exist_ok=True)
    return tl_dir


def _capture_frame(output_path: str, resolution: str | None = None) -> bool:
    """Capture a single JPEG frame from the RTSP stream.

    Returns True on success, False on failure (logged at DEBUG).
    """
    vf = f"scale={resolution}" if resolution and resolution != "original" else None
    cmd = [
        "ffmpeg", "-y",
        "-rtsp_transport", "tcp",
        "-i", RTSP_URL,
        "-frames:v", "1",
        "-q:v", "6",
    ]
    if vf:
        cmd += ["-vf", vf]
    cmd.append(output_path)

    try:
        subprocess.run(cmd, capture_output=True, timeout=10)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        log.debug("Timelapse frame empty: %s", output_path)
    except subprocess.TimeoutExpired:
        log.debug("Timelapse frame capture timed out")
    except Exception as e:
        log.debug("Timelapse frame capture failed: %s", e)

    # Clean up partial file
    try:
        if os.path.exists(output_path):
            os.unlink(output_path)
    except OSError:
        pass
    return False


def _stitch_day(day_dir: str, date_str: str, output_dir: str, fps: int) -> bool:
    """Stitch all JPEGs in day_dir into an MP4. Deletes frames on success."""
    frames = sorted(glob.glob(os.path.join(day_dir, "*.jpg")))
    if not frames:
        log.info("Timelapse stitch skipped (no frames): %s", date_str)
        shutil.rmtree(day_dir, ignore_errors=True)
        return False

    clean_date = date_str.replace("-", "")
    output_path = os.path.join(output_dir, f"timelapse_{clean_date}.mp4")
    log.info("Stitching %d timelapse frames for %s → %s", len(frames), date_str, output_path)

    try:
        subprocess.run(
            [
                "nice", "-n", "19",
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-pattern_type", "glob",
                "-i", os.path.join(day_dir, "*.jpg"),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path,
            ],
            capture_output=True, timeout=600,
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            log.info("Timelapse stitched: %s (%d frames)", output_path, len(frames))
            shutil.rmtree(day_dir, ignore_errors=True)
            return True
        log.error("Timelapse stitch produced empty file: %s", output_path)
    except subprocess.TimeoutExpired:
        log.error("Timelapse stitch timed out for %s", date_str)
    except Exception as e:
        log.error("Timelapse stitch failed for %s: %s", date_str, e)

    return False


def _stitch_pending() -> None:
    """On startup, stitch any previous-day frame directories."""
    tl_dir = _timelapse_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    config = _get_config()
    fps = config.get("fps", 24)

    for entry in sorted(os.listdir(tl_dir)):
        day_dir = os.path.join(tl_dir, entry)
        if not os.path.isdir(day_dir):
            continue
        # Only stitch directories that look like dates and aren't today
        if len(entry) == 10 and entry != today:
            _stitch_day(day_dir, entry, tl_dir, fps)


def _background_loop() -> None:
    global _last_date, _today_frame_count, _last_capture

    # Stitch any leftover days from before this boot
    try:
        _stitch_pending()
    except Exception as e:
        log.error("Timelapse pending stitch failed: %s", e)

    while not _stop_event.is_set():
        config = _get_config()
        if not config.get("enabled", False):
            _stop_event.wait(30)
            continue

        interval = max(1, config.get("interval_minutes", 5)) * 60
        resolution = config.get("resolution", "640x480")
        fps = config.get("fps", 24)
        tl_dir = _timelapse_dir()

        current_date = datetime.now().strftime("%Y-%m-%d")

        # Day rollover — stitch previous day
        if _last_date is not None and current_date != _last_date:
            prev_dir = os.path.join(tl_dir, _last_date)
            if os.path.isdir(prev_dir):
                _stitch_day(prev_dir, _last_date, tl_dir, fps)
            _today_frame_count = 0

        _last_date = current_date

        # Capture today's frame
        day_dir = os.path.join(tl_dir, current_date)
        os.makedirs(day_dir, exist_ok=True)
        frame_name = f"frame_{datetime.now().strftime('%H%M%S')}.jpg"
        frame_path = os.path.join(day_dir, frame_name)

        if _capture_frame(frame_path, resolution):
            _today_frame_count += 1
            _last_capture = datetime.now().isoformat()
            log.debug("Timelapse frame %d: %s", _today_frame_count, frame_name)

        _stop_event.wait(interval)


def start() -> None:
    """Start the timelapse background thread."""
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_background_loop, daemon=True,
                               name="timelapse")
    _thread.start()
    log.info("Timelapse manager started")


def stop() -> None:
    """Stop the timelapse thread gracefully."""
    global _thread
    _stop_event.set()
    if _thread is not None:
        _thread.join(timeout=5)
        _thread = None
    log.info("Timelapse manager stopped")


def restart() -> None:
    """Restart with new settings."""
    stop()
    start()


def get_status() -> dict:
    """Return current timelapse status for the API."""
    config = _get_config()
    return {
        "enabled": config.get("enabled", False),
        "interval_minutes": config.get("interval_minutes", 5),
        "fps": config.get("fps", 24),
        "resolution": config.get("resolution", "640x480"),
        "today_frame_count": _today_frame_count,
        "last_capture": _last_capture,
    }


def get_timelapse_videos() -> list[dict]:
    """List all stitched timelapse MP4s."""
    tl_dir = _timelapse_dir()
    videos = []

    for file in os.listdir(tl_dir):
        if file.startswith("timelapse_") and file.endswith(".mp4"):
            filepath = os.path.join(tl_dir, file)
            # Extract date from filename: timelapse_YYYYMMDD.mp4
            date_part = file.replace("timelapse_", "").replace(".mp4", "")
            date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}" if len(date_part) == 8 else ""
            try:
                size = os.path.getsize(filepath)
            except OSError:
                size = 0
            videos.append({"path": filepath, "date": date_str, "size": size})

    videos.sort(key=lambda v: v["date"], reverse=True)
    return videos


def delete_timelapse(path: str) -> tuple[dict, int]:
    """Delete a timelapse MP4 with safety checks."""
    tl_dir = _timelapse_dir()
    base_dir = os.path.realpath(tl_dir)
    target = os.path.realpath(path)

    try:
        if os.path.commonpath([base_dir, target]) != base_dir:
            return {"error": "Invalid path"}, 400
    except ValueError:
        return {"error": "Invalid path"}, 400

    if not target.endswith(".mp4") or not os.path.basename(target).startswith("timelapse_"):
        return {"error": "Invalid timelapse file"}, 400

    if not os.path.isfile(target):
        return {"error": "Timelapse not found"}, 404

    try:
        os.remove(target)
        log.info("Timelapse deleted: %s", target)
        return {"message": "Timelapse deleted"}, 200
    except Exception as e:
        log.error("Failed to delete timelapse %s: %s", target, e)
        return {"error": str(e)}, 500
