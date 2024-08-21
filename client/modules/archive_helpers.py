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
        