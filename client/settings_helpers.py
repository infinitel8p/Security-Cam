import json
import os

SETTINGS_FILE = './settings/settings.json'

def get_settings():
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    return settings

def update_settings(new_settings):
    with open(SETTINGS_FILE, 'r+') as f:
        settings = json.load(f)
        settings.update(new_settings)
        f.seek(0)
        json.dump(settings, f, indent=4)
        f.truncate()

def is_valid_directory(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    elif os.path.isdir(path) and os.access(path, os.W_OK):
        return True
    else:
        return False

def update_video_save_location(new_location):
    if is_valid_directory(new_location):
        update_settings({"VideoSaveLocation": new_location})
        return True
    else:
        return False
