import logging
import os
import json
import subprocess

log = logging.getLogger("settings")

_SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__))), "settings")
SETTINGS_FILE = os.path.join(_SETTINGS_DIR, "settings.json")
DEFAULTS_FILE = os.path.join(_SETTINGS_DIR, "settings.defaults.json")


def _ensure_settings():
    """Create settings.json from defaults if missing, and merge any new keys."""
    with open(DEFAULTS_FILE, 'r') as f:
        defaults = json.load(f)

    if not os.path.exists(SETTINGS_FILE):
        os.makedirs(_SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(defaults, f, indent=4)
        log.info("Created settings.json from defaults")
        return defaults

    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)

    # Add any new keys from defaults that don't exist yet
    updated = False
    for key, value in defaults.items():
        if key not in settings:
            settings[key] = value
            updated = True

    if updated:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)

    return settings


def get_settings():
    """
    Load and return the settings from the settings file.
    Creates from defaults if missing, merges new default keys.

    Returns:
        Dict[str, Any]: The settings as a dictionary.
    """
    return _ensure_settings()


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
    log.info("Settings updated: %s", list(new_settings.keys()))


##### Bluetooth helper functions #####


def pair_bt_device(device_mac: str) -> bool:
    """Pair and trust a Bluetooth device. Returns True on success."""
    log.info("Pairing BT device %s ...", device_mac)
    current_dir = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(current_dir, "shell/pair.sh")

    if not os.path.exists(script_path):
        log.error("pair.sh not found at %s", script_path)
        raise FileNotFoundError("pair.sh not found")

    subprocess.run(["chmod", "+x", script_path],
                   check=True, capture_output=True, text=True)

    result = subprocess.run(
        [script_path, device_mac], capture_output=True, text=True)

    output = result.stdout.strip()
    log.debug("pair.sh output: %s", output)
    if "Device is already paired" in output:
        log.info("BT device %s already paired", device_mac)
        return True
    if result.returncode != 0:
        log.error("BT pairing failed for %s: %s", device_mac, output or result.stderr.strip())
        raise RuntimeError(f"Pairing failed: {output or result.stderr.strip()}")
    log.info("BT device %s paired and trusted", device_mac)
    return True


def unpair_bt_device(device_mac: str) -> bool:
    """Unpair a Bluetooth device. Returns True on success."""
    log.info("Unpairing BT device %s ...", device_mac)
    current_dir = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(current_dir, "shell/unpair.sh")

    if not os.path.exists(script_path):
        log.error("unpair.sh not found at %s", script_path)
        raise FileNotFoundError("unpair.sh not found")

    subprocess.run(["chmod", "+x", script_path],
                   check=True, capture_output=True, text=True)

    result = subprocess.run(
        [script_path, device_mac], capture_output=True, text=True)

    output = result.stdout.strip()
    log.debug("unpair.sh output: %s", output)
    if "Device not found or already unpaired" in output:
        log.info("BT device %s was already unpaired", device_mac)
        return True
    if result.returncode != 0:
        log.error("BT unpairing failed for %s: %s", device_mac, output or result.stderr.strip())
        raise RuntimeError(f"Unpairing failed: {output or result.stderr.strip()}")
    log.info("BT device %s unpaired", device_mac)
    return True


##### Directory helper functions #####


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
            log.error("Error creating directory %s: %s", path, e)
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
        log.info("Video save location changed to %s", new_location)
        return True
    else:
        log.warning("Invalid video save location: %s", new_location)
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
        log.error("Error listing directories in %s: %s", path, e)
        return None, str(e)
