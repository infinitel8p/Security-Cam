import os
import json
import subprocess

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "settings/settings.json")

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

# Bluetooth helper functions
def pair_bt_device(device_mac: str):
    """
    Pair a Bluetooth device using a shell script.

    Args:
        device_mac (str): The MAC address of the device to pair.

    Raises:
        FileNotFoundError: If the shell script is not found.
        RuntimeError: If the pairing fails.
    """

    current_dir = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(current_dir, "shell/pair.sh")

    try:
        # Check if the file actually exists
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"pair.sh not found")

        # Ensure the shell script is executable
        subprocess.run(["chmod", "+x", script_path], check=True, capture_output=True, text=True)

        # Run the shell script with the MAC address as an argument
        result = subprocess.run(f"{script_path} {device_mac}", capture_output=True, text=True, shell=True)

        # Check if the process was successful
        if result.returncode != 0:
            if "Device is already paired" in result.stdout:
                print("Device is already paired, skipping pairing...")
            else:
                print(f"Script returned non-zero exit code: {result.returncode}")
                print(f"STDOUT: {result.stdout.strip()}")
                print(f"STDERR: {result.stderr.strip()}")
        else:
            # Check for success message or specific output conditions
            if "Pairing successful" in result.stdout:
                print("Pairing was successful!")
            elif "Device is already paired" in result.stdout:
                print("Device is already paired, skipping pairing...")
            elif "trust succeeded" in result.stdout:
                print("Device trusted successfully!")
            else:
                print(f"Unexpected output during pairing: {result.stdout.strip()}")

    except FileNotFoundError as fnf_error:
        print(fnf_error)
    except RuntimeError as re:
        # Print only the error message without traceback
        print(re)
    except Exception as e:
        # Print exception message without traceback
        print(f"An error occurred: {e}")

def unpair_bt_device(device_mac: str):
    """
    Unpair a Bluetooth device using a shell script.

    Args:
        device_mac (str): The MAC address of the device to unpair.

    Raises:
        FileNotFoundError: If the shell script is not found.
        RuntimeError: If the unpairing fails.
    """

    current_dir = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(current_dir, "shell/unpair.sh")

    try:
        # Check if the file actually exists
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"unpair.sh not found")

        # Ensure the shell script is executable
        subprocess.run(["chmod", "+x", script_path], check=True, capture_output=True, text=True)

        # Run the shell script with MAC address as an argument
        result = subprocess.run(f"{script_path} {device_mac}", capture_output=True, text=True, shell=True)

        # Check if the process was successful
        if result.returncode != 0:
            if "Device not found or already unpaired" in result.stdout:
                print("Device not found or already unpaired.")
            else:
                print(f"Script returned non-zero exit code: {result.returncode}")
                print(f"STDOUT: {result.stdout.strip()}")
                print(f"STDERR: {result.stderr.strip()}")
        else:
            # Check for success message
            if "Unpairing successful" in result.stdout:
                print("Unpairing was successful!")
            else:
                print(f"Unexpected output during unpairing: {result.stdout.strip()}")

    except FileNotFoundError as fnf_error:
        print(fnf_error)
    except RuntimeError as re:
        # Print only the error message without traceback
        print(re)
    except Exception as e:
        # Print exception message without traceback
        print(f"An error occurred: {e}")

# Directory helper functions
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