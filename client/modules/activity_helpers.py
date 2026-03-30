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


def scan_bt_devices(duration: int = 10) -> list[dict]:
    """Discover nearby Bluetooth devices using bluetoothctl.

    Uses bluetoothctl which discovers both classic and BLE devices (including
    iPhones), unlike pybluez which only finds classic Bluetooth.

    Returns a list of {"address": "...", "name": "..."} dicts.
    """
    try:
        # Start scan, wait for duration, then list discovered devices
        subprocess.run(
            ["sudo", "bluetoothctl", "scan", "on"],
            timeout=duration, capture_output=True
        )
    except subprocess.TimeoutExpired:
        pass  # Expected — scan runs until timeout
    except Exception as e:
        logging.error(f"Bluetooth scan start failed: {e}")
        raise RuntimeError(f"Bluetooth scan failed: {e}")

    try:
        subprocess.run(
            ["sudo", "bluetoothctl", "scan", "off"],
            timeout=5, capture_output=True
        )
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["sudo", "bluetoothctl", "devices"],
            capture_output=True, text=True, timeout=5
        )
        devices = []
        seen = set()
        for line in result.stdout.strip().splitlines():
            # Format: "Device AA:BB:CC:DD:EE:FF DeviceName"
            match = re.match(r"Device\s+([0-9A-Fa-f:]{17})\s+(.*)", line)
            if match:
                addr = match.group(1)
                name = match.group(2).strip() or addr
                if addr.upper() not in seen:
                    seen.add(addr.upper())
                    devices.append({"address": addr, "name": name})
        return devices
    except Exception as e:
        logging.error(f"Bluetooth device listing failed: {e}")
        raise RuntimeError(f"Bluetooth scan failed: {e}")


def get_bt_device_status(address: str) -> bool:
    """Check if a specific Bluetooth device is reachable."""
    try:
        status = bluetooth.lookup_name(address, timeout=3)
        return status is not None
    except Exception:
        return False


def get_device_statuses() -> dict:
    """Return online/offline status for all configured BT and WiFi devices.

    Returns {"bt": {"AA:BB:...": True/False}, "wifi": {"AA:BB:...": True/False}}
    """
    settings = settings_helpers.get_settings()
    result = {"bt": {}, "wifi": {}}

    # Bluetooth: check each device
    for device in settings.get("TARGET_BT_ADDRESSES", []):
        addr = device["address"]
        result["bt"][addr.upper()] = get_bt_device_status(addr)

    # WiFi: get connected AP stations and match against targets
    ap_stations = set()
    if is_in_ap_mode():
        try:
            output = subprocess.check_output(
                "iw dev ap0 station dump", shell=True
            ).decode("utf-8").strip().lower()
            ap_stations = set(re.findall(r"station\s+([0-9a-f:]{17})", output))
        except Exception:
            pass

    for device in settings.get("TARGET_AP_MAC_ADDRESSES", []):
        addr = device["address"]
        result["wifi"][addr.upper()] = addr.lower() in ap_stations

    return result


def is_in_ap_mode() -> bool:
    """Check if the device is in AP mode."""
    try:
        output = subprocess.check_output(
            "ip addr show ap0 | grep '192.168.4.1'", shell=True).decode('utf-8').strip()
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
