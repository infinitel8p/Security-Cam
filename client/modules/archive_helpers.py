import os
from . import settings_helpers

settings = settings_helpers.get_settings()

def get_videos():
    reload_settings()
    video_dir = settings["VideoSaveLocation"]
    videos = []

    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if file.endswith(".mp4") and not file.endswith(".tmp.mp4"):
                videos.append(os.path.join(root, file))

    # Sort newest first by modification time
    videos.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return videos


def reload_settings():
    global settings
    settings = settings_helpers.get_settings()
        
def delete_video(video_path):
    if not video_path or not os.path.exists(video_path):
        return {"error": "Video not found"}, 404

    try:
        os.remove(video_path)
        return {"message": "Video deleted successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500