import logging
import re
import bluetooth
import subprocess
from . import settings_helpers


def is_device_connected_to_bt() -> bool:
    """Check if any of the target Bluetooth addresses are visible."""
    settings = settings_helpers.get_settings()
    for addr in settings.get("TARGET_BT_ADDRESSES", []):
        status = bluetooth.lookup_name(addr["address"], timeout=3)
        if status:
            logging.info(f"Device {addr['name']} is connected.")
            return True
    logging.warning("No devices connected via Bluetooth.")
    return False


def scan_bt_devices(duration: int = 8) -> list[dict]:
    """Discover nearby Bluetooth devices.

    Returns a list of {"address": "...", "name": "..."} dicts.
    """
    try:
        found = bluetooth.discover_devices(
            duration=duration, lookup_names=True, lookup_class=False
        )
        return [{"address": addr, "name": name or addr} for addr, name in found]
    except Exception as e:
        logging.error(f"Bluetooth scan failed: {e}")
        raise RuntimeError(f"Bluetooth scan failed: {e}")


def is_in_ap_mode() -> bool:
    """Check if the device is in AP mode."""
    try:
        output = subprocess.check_output(
            "ip addr show ap0 | grep '192.168.10.1'", shell=True).decode('utf-8').strip()
        return bool(output)
    except Exception:
        return False


def get_ap_stations() -> list[dict]:
    """List MAC addresses currently connected to the AP.

    Returns a list of {"address": "...", "name": null} dicts.
    """
    if not is_in_ap_mode():
        return []

    try:
        output = subprocess.check_output(
            "iw dev ap0 station dump", shell=True).decode('utf-8').strip()
        macs = re.findall(r"Station\s+([0-9a-fA-F:]{17})", output)
        return [{"address": mac, "name": None} for mac in macs]
    except Exception as e:
        logging.error(f"Error listing AP stations: {e}")
        return []


def is_device_connected_to_ap() -> bool:
    """Check if any target MAC addresses are connected to the AP."""
    settings = settings_helpers.get_settings()
    if not is_in_ap_mode():
        logging.warning("Device is not in AP mode.")
        return False

    try:
        output = subprocess.check_output(
            "iw dev ap0 station dump", shell=True).decode('utf-8').strip()

        for device in settings.get("TARGET_AP_MAC_ADDRESSES", []):
            if device["address"].lower() in output.lower():
                logging.info(f"Device with MAC address {device['address']} is connected to AP.")
                return True
        logging.warning("No devices connected to AP.")
        return False
    except Exception as e:
        logging.error(f"Error checking connected devices: {e}")
        return False
