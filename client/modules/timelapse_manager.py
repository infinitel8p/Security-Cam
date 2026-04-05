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
from . import sse

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


def _camera_overlay_enabled() -> bool:
    """Check whether MediaMTX's hardware text overlay is active."""
    try:
        from modules import mediamtx_helpers
        import yaml
        with open(mediamtx_helpers.CONFIG_PATH, "r") as f:
            cfg = yaml.safe_load(f)
        cam = cfg.get("paths", {}).get("cam", {})
        return bool(cam.get("rpiCameraTextOverlayEnable", False))
    except Exception:
        return False


def _capture_frame(output_path: str, resolution: str | None = None) -> bool:
    """Capture a single JPEG frame from the RTSP stream.

    If the camera's hardware text overlay is disabled, burns a timestamp
    via FFmpeg drawtext so timelapse frames always have one.  Returns
    True on success, False on failure (logged at DEBUG).
    """
    filters = []
    if resolution and resolution != "original":
        filters.append(f"scale={resolution}")

    if not _camera_overlay_enabled():
        now = datetime.now()
        timestamp_text = now.strftime("%Y-%m-%d  %H\\:%M\\:%S")
        filters.append(
            f"drawtext=text='{timestamp_text}'"
            ":fontsize=16:fontcolor=white:borderw=2:bordercolor=black"
            ":x=8:y=h-th-8"
        )

    cmd = [
        "ffmpeg", "-y",
        "-rtsp_transport", "tcp",
        "-i", RTSP_URL,
        "-frames:v", "1",
        "-q:v", "6",
    ]
    if filters:
        cmd += ["-vf", ",".join(filters)]
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


def _probe_duration(video_path: str) -> float | None:
    """Get video duration in seconds via ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return round(float(result.stdout.strip()), 1)
    except Exception as e:
        log.debug("ffprobe failed for %s: %s", video_path, e)
    return None


def _write_timelapse_meta(video_path: str, frame_count: int, duration: float | None) -> None:
    """Write a .meta.json sidecar for a stitched timelapse."""
    import json, tempfile
    meta: dict = {"reason": "timelapse", "frame_count": frame_count}
    if duration is not None:
        meta["duration_seconds"] = duration
    meta_path = os.path.splitext(video_path)[0] + ".meta.json"
    try:
        dirpath = os.path.dirname(meta_path) or "."
        fd, tmp = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(meta, f, indent=2)
        os.replace(tmp, meta_path)
    except Exception as e:
        log.debug("Failed to write timelapse meta %s: %s", meta_path, e)


def _read_timelapse_meta(video_path: str) -> dict | None:
    """Read a .meta.json sidecar for a timelapse."""
    import json
    meta_path = os.path.splitext(video_path)[0] + ".meta.json"
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _generate_thumbnail(video_path: str) -> None:
    """Extract a frame from a few seconds into the video as a poster thumbnail."""
    thumb_path = os.path.splitext(video_path)[0] + ".thumb.jpg"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", "3",
                "-i", video_path,
                "-frames:v", "1",
                "-vf", "scale=320:-1",
                "-q:v", "6",
                thumb_path,
            ],
            capture_output=True, timeout=30,
        )
        if not (os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0):
            # Very short timelapse - try first frame
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-frames:v", "1",
                    "-vf", "scale=320:-1",
                    "-q:v", "6",
                    thumb_path,
                ],
                capture_output=True, timeout=30,
            )
        if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            log.info("Timelapse thumbnail generated: %s", thumb_path)
    except Exception as e:
        log.debug("Timelapse thumbnail failed for %s: %s", video_path, e)


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
            duration = _probe_duration(output_path)
            _write_timelapse_meta(output_path, len(frames), duration)
            _generate_thumbnail(output_path)
            sse.emit("archive_updated", {"path": output_path, "type": "timelapse"})
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


def _restore_today_count() -> None:
    """Restore the frame count for today from existing files on disk."""
    global _today_frame_count, _last_date, _last_capture
    tl_dir = _timelapse_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = os.path.join(tl_dir, today)
    _last_date = today
    if os.path.isdir(today_dir):
        frames = [f for f in os.listdir(today_dir) if f.endswith(".jpg")]
        _today_frame_count = len(frames)
        if frames:
            _last_capture = datetime.now().isoformat()
            log.info("Restored timelapse state: %d frames for %s", _today_frame_count, today)


def _background_loop() -> None:
    global _last_date, _today_frame_count, _last_capture

    # Restore count from existing frames on disk
    try:
        _restore_today_count()
    except Exception as e:
        log.error("Timelapse state restore failed: %s", e)

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

        # Day rollover - stitch previous day
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
            log.info("Timelapse frame %d captured: %s", _today_frame_count, frame_name)

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
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            except OSError:
                size = 0
                mtime = ""
            entry: dict = {"path": filepath, "date": date_str, "size": size, "mtime": mtime}
            # Read metadata sidecar (duration, frame count)
            meta = _read_timelapse_meta(filepath)
            if meta and "duration_seconds" in meta:
                entry["duration_seconds"] = meta["duration_seconds"]
            if meta and "frame_count" in meta:
                entry["frame_count"] = meta["frame_count"]
            # Check for thumbnail sidecar
            thumb_path = os.path.splitext(filepath)[0] + ".thumb.jpg"
            if os.path.exists(thumb_path):
                entry["thumbnail"] = thumb_path
            videos.append(entry)

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
        # Clean up sidecar files
        for ext in (".thumb.jpg", ".meta.json"):
            sidecar = os.path.splitext(target)[0] + ext
            if os.path.exists(sidecar):
                os.remove(sidecar)
        log.info("Timelapse deleted: %s", target)
        return {"message": "Timelapse deleted"}, 200
    except Exception as e:
        log.error("Failed to delete timelapse %s: %s", target, e)
        return {"error": str(e)}, 500
