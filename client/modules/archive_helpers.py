import json
import logging
import os
import time
from . import settings_helpers

log = logging.getLogger("archive")
settings = settings_helpers.get_settings()

# TTL cache to avoid full filesystem scans on every request
_cache: dict = {}
_CACHE_TTL = 30  # seconds


def invalidate_cache():
    """Clear the archive cache. Call after recording stop, delete, etc."""
    _cache.clear()


def _get_cached(key: str, loader):
    now = time.monotonic()
    entry = _cache.get(key)
    if entry and (now - entry[1]) < _CACHE_TTL:
        return entry[0]
    result = loader()
    _cache[key] = (result, now)
    return result


def get_videos():
    reload_settings()
    return _get_cached("videos", _scan_videos)


def get_video_count() -> int:
    """Return total number of videos using the cached list."""
    return len(get_videos())


def _scan_videos():
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

                # Check for sprite sheet
                spr_path = os.path.splitext(filepath)[0] + ".sprite.jpg"
                if os.path.exists(spr_path):
                    entry["sprite"] = spr_path

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


def get_snapshots():
    """List all snapshot JPEG files in the recordings directory."""
    reload_settings()
    return _get_cached("snapshots", _scan_snapshots)


def _scan_snapshots():
    video_dir = settings["VideoSaveLocation"]
    snapshots = []

    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if file.startswith("snapshot_") and file.endswith(".jpg"):
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                except OSError:
                    size = 0
                snapshots.append({"path": filepath, "size": size})

    snapshots.sort(key=lambda s: os.path.getmtime(s["path"]), reverse=True)
    return snapshots


def delete_snapshot(snapshot_path):
    """Delete a snapshot JPEG. Same safety checks as delete_video."""
    reload_settings()
    video_dir = settings.get("VideoSaveLocation")
    if not video_dir:
        return {"error": "Video storage location not configured"}, 500

    if not snapshot_path:
        return {"error": "Snapshot not found"}, 404

    base_dir = os.path.realpath(video_dir)
    target = os.path.realpath(snapshot_path)

    try:
        if os.path.commonpath([base_dir, target]) != base_dir:
            log.warning("Delete blocked - path outside VideoSaveLocation: %s", snapshot_path)
            return {"error": "Invalid snapshot path"}, 400
    except ValueError:
        return {"error": "Invalid snapshot path"}, 400

    if not target.endswith(".jpg") or not os.path.basename(target).startswith("snapshot_"):
        log.warning("Delete blocked - not a snapshot file: %s", snapshot_path)
        return {"error": "Invalid snapshot file"}, 400

    if not os.path.isfile(target):
        return {"error": "Snapshot not found"}, 404

    try:
        os.remove(target)
        invalidate_cache()
        log.info("Snapshot deleted: %s", target)
        return {"message": "Snapshot deleted"}, 200
    except Exception as e:
        log.error("Failed to delete snapshot %s: %s", target, e)
        return {"error": str(e)}, 500


def reload_settings():
    global settings
    prev = settings.get("VideoSaveLocation")
    settings = settings_helpers.get_settings()
    if settings.get("VideoSaveLocation") != prev:
        invalidate_cache()

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
        for ext in (".meta.json", ".thumb.jpg", ".sprite.jpg"):
            sidecar = os.path.splitext(target)[0] + ext
            if os.path.exists(sidecar):
                os.remove(sidecar)
        invalidate_cache()
        log.info("Video deleted: %s", target)
        return {"message": "Video deleted successfully"}, 200
    except Exception as e:
        log.error("Failed to delete video %s: %s", target, e)
        return {"error": str(e)}, 500
