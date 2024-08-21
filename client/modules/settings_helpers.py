import json
import os

SETTINGS_FILE = './settings/settings.json'

def get_settings():
    """
    Load and return the settings from the settings file.

    Returns:
        Dict[str, Any]: The settings as a dictionary.
    """
    
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    return settings

def update_settings(new_settings) -> None:
    """
    Update the settings in the settings file with new values.

    Args:
        new_settings (Dict[str, Any]): The new settings to be updated.
    """

    with open(SETTINGS_FILE, 'r+') as f:
        settings = json.load(f)
        settings.update(new_settings)
        f.seek(0)
        json.dump(settings, f, indent=4)
        f.truncate()

def is_directory(path: str) -> bool:
    """
    Check if a given path is a valid directory.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is a valid directory, False otherwise.
    """

    return os.path.isdir(path)

def is_valid_directory(path: str) -> bool:
    """
    Check if the provided path is a valid directory. If it does not exist,
    attempt to create it.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is a valid directory or was successfully created,
              False otherwise.
    """

    if not os.path.exists(path):
        try:
            os.makedirs(path)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    elif is_directory(path) and os.access(path, os.W_OK):
        return True
    else:
        return False

def update_video_save_location(new_location: str) -> bool:
    """
    Update the video save location in the settings if the provided directory is valid.

    Args:
        new_location (str): The new directory path to save videos.

    Returns:
        bool: True if the location was updated successfully, False otherwise.
    """

    if is_valid_directory(new_location):
        update_settings({"VideoSaveLocation": new_location})
        return True
    else:
        return False

def list_directories(path: str = "./"):
    """
    List directories within the provided path.

    Args:
        path (str): The path to list directories in. Defaults to the current directory.

    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[str]]: A tuple containing a dictionary
        with the list of directories and the current path if successful, or an error
        message if an exception occurs.
    """

    try:
        directories = [
            {"name": name, "path": os.path.join(path, name)}
            for name in os.listdir(path)
            if is_directory(os.path.join(path, name))
        ]
        return {"directories": directories, "current_path": path}, None
    except Exception as e:
        print(f"Error listing directories: {e}")
        return None, str(e)