import os
import subprocess
import threading
from datetime import datetime
from . import settings_helpers

settings = settings_helpers.get_settings()

lock = threading.Lock()
_ffmpeg_process = None
is_recording = False
recorded_filename = None

RTSP_URL = "rtsp://localhost:8554/cam"


def reload_settings():
    global settings
    settings = settings_helpers.get_settings()


def start_recording() -> None:
    global _ffmpeg_process, is_recording, recorded_filename

    reload_settings()

    video_save_location = settings.get('VideoSaveLocation', './recordings')
    os.makedirs(video_save_location, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    recorded_filename = os.path.join(video_save_location, f'output_{timestamp}.mp4')

    with lock:
        if is_recording:
            return

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
        is_recording = True
        print(f"Recording started: {recorded_filename}")


def stop_recording() -> None:
    global _ffmpeg_process, is_recording, recorded_filename

    with lock:
        if _ffmpeg_process is None:
            return

        # Send 'q' to ffmpeg for a graceful stop (writes proper file trailer)
        try:
            _ffmpeg_process.stdin.write(b"q")
            _ffmpeg_process.stdin.flush()
        except BrokenPipeError:
            pass

        proc = _ffmpeg_process
        filename = recorded_filename
        _ffmpeg_process = None
        is_recording = False

    # Wait for ffmpeg to finish outside the lock
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    # Re-mux with faststart for browser seeking support
    if filename and os.path.exists(filename) and os.path.getsize(filename) > 0:
        threading.Thread(target=_fix_faststart, args=(filename,)).start()

    print(f"Recording stopped: {filename}")


def _fix_faststart(file_path: str) -> None:
    """Re-mux to move moov atom to start for browser playback."""
    tmp_path = file_path + ".tmp.mp4"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", file_path, "-c", "copy", "-movflags", "+faststart", tmp_path],
            check=True, capture_output=True,
        )
        os.replace(tmp_path, file_path)
        print(f"Faststart applied: {file_path}")
    except Exception as e:
        print(f"Failed to apply faststart: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
