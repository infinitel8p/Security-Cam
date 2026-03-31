import json
import logging
import os
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from . import settings_helpers

log = logging.getLogger("stream")
settings = settings_helpers.get_settings()

lock = threading.Lock()
_ffmpeg_process = None
is_recording = False
recorded_filename = None
_recording_start_time = None
_recording_reason = None
_watchdog_thread = None
_on_crash_callback = None  # Called when ffmpeg dies unexpectedly

RTSP_URL = "rtsp://localhost:8554/cam"
_WATCHDOG_INTERVAL = 3  # seconds between health checks


def set_on_crash(callback):
    """Register a callback for ffmpeg crash. Called with no arguments."""
    global _on_crash_callback
    _on_crash_callback = callback


def reload_settings():
    global settings
    settings = settings_helpers.get_settings()


def _watchdog():
    """Monitor ffmpeg health and clean up if it dies unexpectedly."""
    while True:
        time.sleep(_WATCHDOG_INTERVAL)
        with lock:
            if not is_recording or _ffmpeg_process is None:
                return  # Recording ended normally, exit watchdog
            if _ffmpeg_process.poll() is not None:
                # ffmpeg died - clean up state
                code = _ffmpeg_process.returncode
                log.error("FFmpeg died unexpectedly (code=%d), resetting recording state", code)
                _cleanup_dead_recording()
                return


def _cleanup_dead_recording():
    """Reset recording state after ffmpeg crash. Caller must hold lock."""
    global _ffmpeg_process, is_recording, recorded_filename
    global _recording_start_time, _recording_reason

    filename = recorded_filename
    start_time = _recording_start_time

    _ffmpeg_process = None
    is_recording = False
    _recording_start_time = None
    _recording_reason = None

    # Update metadata with what we know
    if filename and start_time:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        meta = _read_meta(filename) or {}
        meta["stopped"] = datetime.now(timezone.utc).isoformat()
        meta["duration_seconds"] = round(duration, 1)
        meta["crash"] = True
        _write_meta(filename, meta)

    # Notify listener (sensor_manager) so it can reset _sensor_recording
    if _on_crash_callback:
        try:
            _on_crash_callback()
        except Exception as e:
            log.error("Crash callback failed: %s", e)


def _meta_path(video_path: str) -> str:
    """Return the .meta.json sidecar path for a video file."""
    return os.path.splitext(video_path)[0] + ".meta.json"


def _write_meta(video_path: str, meta: dict) -> None:
    """Write recording metadata to a sidecar JSON file atomically."""
    path = _meta_path(video_path)
    dirpath = os.path.dirname(path) or "."
    try:
        fd, tmp = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(meta, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception as e:
        log.error("Failed to write metadata %s: %s", path, e)
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _read_meta(video_path: str) -> dict | None:
    """Read recording metadata from a sidecar JSON file."""
    path = _meta_path(video_path)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def start_recording(reason: str = "manual", sensor_type: str | None = None) -> None:
    global _ffmpeg_process, is_recording, recorded_filename
    global _recording_start_time, _recording_reason

    reload_settings()

    video_save_location = settings.get('VideoSaveLocation', './recordings')
    os.makedirs(video_save_location, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    recorded_filename = os.path.join(video_save_location, f'output_{timestamp}.mp4')

    with lock:
        if is_recording:
            log.warning("start_recording called but already recording")
            return

        log.info("Starting FFmpeg recording → %s", recorded_filename)
        _ffmpeg_process = subprocess.Popen(
            [
                "ffmpeg", "-y",
                "-rtsp_transport", "tcp",
                "-i", RTSP_URL,
                "-c", "copy",
                "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
                recorded_filename,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Verify FFmpeg is actually running before reporting success
        time.sleep(0.5)
        if _ffmpeg_process.poll() is not None:
            log.error("FFmpeg exited immediately (code=%d)", _ffmpeg_process.returncode)
            _ffmpeg_process = None
            return
        is_recording = True
        _recording_start_time = datetime.now(timezone.utc)
        _recording_reason = reason

        # Write initial metadata
        meta = {
            "reason": reason,
            "started": _recording_start_time.isoformat(),
        }
        if sensor_type:
            meta["sensor_type"] = sensor_type
        _write_meta(recorded_filename, meta)

        log.info("Recording started: %s (pid=%d, reason=%s)",
                 recorded_filename, _ffmpeg_process.pid, reason)

    # Start watchdog outside the lock
    global _watchdog_thread
    _watchdog_thread = threading.Thread(target=_watchdog, daemon=True)
    _watchdog_thread.start()


def stop_recording() -> None:
    global _ffmpeg_process, is_recording, recorded_filename
    global _recording_start_time, _recording_reason

    with lock:
        if _ffmpeg_process is None:
            log.warning("stop_recording called but not recording")
            return

        log.info("Stopping FFmpeg (pid=%d)...", _ffmpeg_process.pid)
        # Send 'q' to ffmpeg for a graceful stop (writes proper file trailer)
        try:
            _ffmpeg_process.stdin.write(b"q")
            _ffmpeg_process.stdin.flush()
        except BrokenPipeError:
            log.warning("FFmpeg stdin pipe already broken")

        proc = _ffmpeg_process
        filename = recorded_filename
        start_time = _recording_start_time
        _ffmpeg_process = None
        is_recording = False
        _recording_start_time = None
        _recording_reason = None

    # Wait for ffmpeg to finish outside the lock
    try:
        proc.wait(timeout=10)
        log.info("FFmpeg exited cleanly (code=%d)", proc.returncode)
    except subprocess.TimeoutExpired:
        log.warning("FFmpeg did not exit in 10s, killing")
        proc.kill()
        proc.wait()

    # Update metadata with duration
    if filename and start_time:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        meta = _read_meta(filename) or {}
        meta["stopped"] = datetime.now(timezone.utc).isoformat()
        meta["duration_seconds"] = round(duration, 1)
        _write_meta(filename, meta)

    # Re-mux with faststart for browser seeking support
    if filename and os.path.exists(filename) and os.path.getsize(filename) > 0:
        log.info("Queuing faststart fix for %s", filename)
        threading.Thread(target=_fix_faststart, args=(filename,)).start()

    log.info("Recording stopped: %s", filename)


def _fix_faststart(file_path: str) -> None:
    """Re-mux to move moov atom to start for browser playback."""
    tmp_path = file_path + ".tmp.mp4"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", file_path, "-c", "copy", "-movflags", "+faststart", tmp_path],
            check=True, capture_output=True, timeout=60,
        )
        os.replace(tmp_path, file_path)
        log.info("Faststart applied: %s", file_path)
    except Exception as e:
        log.error("Failed to apply faststart for %s: %s", file_path, e)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
