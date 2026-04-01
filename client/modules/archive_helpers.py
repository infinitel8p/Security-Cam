import json
import logging
import os
from . import settings_helpers

log = logging.getLogger("archive")
settings = settings_helpers.get_settings()

def get_videos():
    reload_settings()
    video_dir = settings["VideoSaveLocation"]
    videos = []

    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if file.endswith(".mp4") and not file.endswith(".tmp.mp4"):
                filepath = os.path.join(root, file)
                entry = {"path": filepath}

                # Load sidecar metadata if it exists
                meta_path = os.path.splitext(filepath)[0] + ".meta.json"
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r") as f:
                            entry["meta"] = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        pass

                # Check for thumbnail
                thumb_path = os.path.splitext(filepath)[0] + ".thumb.jpg"
                if os.path.exists(thumb_path):
                    entry["thumbnail"] = thumb_path

                videos.append(entry)

    # Sort newest first by modification time
    videos.sort(key=lambda v: os.path.getmtime(v["path"]), reverse=True)
    return videos


def count_videos_since(since_iso: str) -> int:
    """Count recordings created after the given ISO timestamp."""
    from datetime import datetime, timezone
    try:
        since = datetime.fromisoformat(since_iso)
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return 0

    reload_settings()
    video_dir = settings["VideoSaveLocation"]
    count = 0
    since_ts = since.timestamp()

    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if file.endswith(".mp4") and not file.endswith(".tmp.mp4"):
                filepath = os.path.join(root, file)
                try:
                    if os.path.getmtime(filepath) > since_ts:
                        count += 1
                except OSError:
                    pass
    return count


def reload_settings():
    global settings
    settings = settings_helpers.get_settings()
        
def delete_video(video_path):
    reload_settings()
    video_dir = settings.get("VideoSaveLocation")
    if not video_dir:
        log.error("VideoSaveLocation is not configured")
        return {"error": "Video storage location not configured"}, 500

    if not video_path:
        return {"error": "Video not found"}, 404

    # Resolve to absolute paths to prevent path traversal
    base_dir = os.path.realpath(video_dir)
    target = os.path.realpath(video_path)

    # Ensure target is inside the configured video directory
    try:
        if os.path.commonpath([base_dir, target]) != base_dir:
            log.warning("Delete blocked - path outside VideoSaveLocation: %s", video_path)
            return {"error": "Invalid video path"}, 400
    except ValueError:
        log.warning("Delete blocked - incompatible path: %s", video_path)
        return {"error": "Invalid video path"}, 400

    # Only allow .mp4 files (not temp files)
    if not target.endswith(".mp4") or target.endswith(".tmp.mp4"):
        log.warning("Delete blocked - not a video file: %s", video_path)
        return {"error": "Invalid video file"}, 400

    if not os.path.isfile(target):
        log.warning("Delete requested for missing video: %s", video_path)
        return {"error": "Video not found"}, 404

    try:
        os.remove(target)
        # Remove sidecar files (metadata, thumbnail) if they exist
        for ext in (".meta.json", ".thumb.jpg"):
            sidecar = os.path.splitext(target)[0] + ext
            if os.path.exists(sidecar):
                os.remove(sidecar)
        log.info("Video deleted: %s", target)
        return {"message": "Video deleted successfully"}, 200
    except Exception as e:
        log.error("Failed to delete video %s: %s", target, e)
        return {"error": str(e)}, 500
