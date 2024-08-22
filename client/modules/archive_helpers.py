import json
import os

SETTINGS_FILE = './settings/settings.json'

def get_videos():
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    
    video_dir = settings["VideoSaveLocation"]
    videos = []

    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if file.endswith(".mp4"):
                videos.append(os.path.join(root, file))

    return videos
        
def delete_video(video_path):
    if not video_path or not os.path.exists(video_path):
        return {"error": "Video not found"}, 404

    try:
        os.remove(video_path)
        return {"message": "Video deleted successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500