import logging
import bluetooth
import subprocess
from . import settings_helpers

settings = settings_helpers.get_settings()

def is_device_connected_to_bt() -> bool:
    """Check if any of the given Bluetooth addresses are visible."""
    for addr in settings.get("TARGET_BT_ADDRESSES"):
        status = bluetooth.lookup_name(addr["address"], timeout=3)
        if status:
            logging.info(f"Device {addr['name']} is connected.")
            return True
    logging.warning("No devices connected via Bluetooth.")
    return False

def is_in_ap_mode() -> bool:
    """Check if the device is in AP mode."""
    try:
        output = subprocess.check_output(
            "ip addr show ap0 | grep '192.168.10.1'", shell=True).decode('utf-8').strip()
        return bool(output)
    except Exception:
        return False


def is_device_connected_to_ap(mac_addresses) -> bool:
    """Check if any of the given MAC addresses are connected to the AP."""
    if not is_in_ap_mode():
        logging.warning("Device is not in AP mode.")
        return False

    try:
        # Use the 'iw' command to get a list of connected devices
        output = subprocess.check_output(
            "iw dev ap0 station dump", shell=True).decode('utf-8').strip()

        for mac in mac_addresses:
            if mac in output:
                logging.info(
                    f"Device with MAC address {mac} is connected to AP.")
                return True
        logging.warning("No devices connected to AP.")
        return False
    except Exception as e:
        logging.error(f"Error checking connected devices: {e}")
        return False
