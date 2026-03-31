import logging
import re
import bluetooth
import subprocess
from . import settings_helpers

log = logging.getLogger("wifi")
bt_log = logging.getLogger("bt.scan")


def is_device_connected_to_bt() -> bool:
    """Check if any of the target Bluetooth addresses are visible."""
    settings = settings_helpers.get_settings()
    for addr in settings.get("TARGET_BT_ADDRESSES", []):
        status = bluetooth.lookup_name(addr["address"], timeout=3)
        if status:
            bt_log.info("Device %s (%s) is nearby", addr["name"], addr["address"])
            return True
    bt_log.debug("No target devices detected")
    return False


def scan_bt_devices(duration: int = 20) -> list[dict]:
    """Discover nearby Bluetooth devices using bluetoothctl.

    Uses bluetoothctl which discovers both classic and BLE devices (including
    iPhones), unlike pybluez which only finds classic Bluetooth.

    Runs scan for `duration` seconds (default 20s for reliable BLE discovery),
    collecting devices as they appear in the scan output, then also queries
    the full device list.

    Returns a list of {"address": "...", "name": "..."} dicts.
    """
    bt_log.info("Scan starting (%ds)...", duration)

    # Collect devices from scan output in real-time
    scan_output = ""
    try:
        proc = subprocess.Popen(
            ["sudo", "bluetoothctl", "--timeout", str(duration), "scan", "on"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        scan_output, _ = proc.communicate(timeout=duration + 5)
    except subprocess.TimeoutExpired:
        if proc:
            proc.kill()
            scan_output, _ = proc.communicate()
    except Exception as e:
        bt_log.error("Scan failed: %s", e)
        raise RuntimeError(f"Bluetooth scan failed: {e}")

    # Also get the full device list (includes cached + just-discovered)
    devices_output = ""
    try:
        result = subprocess.run(
            ["sudo", "bluetoothctl", "devices"],
            capture_output=True, text=True, timeout=5
        )
        devices_output = result.stdout
    except Exception as e:
        bt_log.error("Device listing failed: %s", e)

    # Parse both outputs for device addresses and names
    devices = []
    seen = set()
    combined = scan_output + "\n" + devices_output

    for match in re.finditer(r"Device\s+([0-9A-Fa-f:]{17})\s+(.*)", combined):
        addr = match.group(1)
        name = match.group(2).strip()
        key = addr.upper()
        # Skip unnamed devices and duplicates
        if key not in seen and name and name != addr:
            seen.add(key)
            devices.append({"address": addr, "name": name})

    # Second pass: add devices that only have an address (no resolved name)
    for match in re.finditer(r"Device\s+([0-9A-Fa-f:]{17})\s*(.*)", combined):
        addr = match.group(1)
        key = addr.upper()
        if key not in seen:
            seen.add(key)
            devices.append({"address": addr, "name": addr})

    bt_log.info("Scan found %d device(s)", len(devices))
    return devices


def get_bt_device_status(address: str) -> bool:
    """Check if a specific Bluetooth device is reachable."""
    try:
        status = bluetooth.lookup_name(address, timeout=3)
        return status is not None
    except Exception as e:
        bt_log.error("Status check failed for %s: %s", address, e)
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

    log.debug("Device statuses: %s", result)
    return result


def is_in_ap_mode() -> bool:
    """Check if the device is in AP mode."""
    try:
        output = subprocess.check_output(
            "ip addr show ap0 | grep '192.168.4.1'", shell=True).decode('utf-8').strip()
        return bool(output)
    except Exception:
        log.debug("AP mode check: ap0 interface not found or no 192.168.4.1")
        return False


def _get_dhcp_hostnames() -> dict:
    """Read dnsmasq lease file to map MAC addresses to hostnames.

    dnsmasq lease format: <expiry> <mac> <ip> <hostname> <client-id>
    Returns {"aa:bb:cc:dd:ee:ff": "hostname", ...} (lowercase MACs).
    """
    lease_paths = [
        "/var/lib/misc/dnsmasq.leases",
        "/var/lib/dnsmasq/dnsmasq.leases",
        "/tmp/dnsmasq.leases",
    ]
    for path in lease_paths:
        try:
            with open(path, "r") as f:
                leases = {}
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        mac = parts[1].lower()
                        hostname = parts[3]
                        if hostname != "*":
                            leases[mac] = hostname
                log.debug("Read %d DHCP leases from %s", len(leases), path)
                return leases
        except FileNotFoundError:
            continue
        except Exception as e:
            log.debug("Could not read DHCP leases from %s: %s", path, e)
    return {}


def get_ap_stations() -> list[dict]:
    """List devices currently connected to the AP.

    Returns a list of {"address": "...", "name": "..."} dicts.
    Names are resolved from dnsmasq DHCP leases when available.
    """
    if not is_in_ap_mode():
        return []

    try:
        output = subprocess.check_output(
            "iw dev ap0 station dump", shell=True).decode('utf-8').strip()
        macs = re.findall(r"Station\s+([0-9a-fA-F:]{17})", output)
        log.info("AP has %d connected station(s)", len(macs))

        hostnames = _get_dhcp_hostnames()
        stations = []
        for mac in macs:
            name = hostnames.get(mac.lower())
            stations.append({"address": mac, "name": name})
            if name:
                log.debug("Resolved AP station %s → %s", mac, name)

        return stations
    except Exception as e:
        log.error("Error listing AP stations: %s", e)
        return []


def is_device_connected_to_ap() -> bool:
    """Check if any target MAC addresses are connected to the AP."""
    settings = settings_helpers.get_settings()
    if not is_in_ap_mode():
        log.debug("AP presence check skipped - not in AP mode")
        return False

    try:
        output = subprocess.check_output(
            "iw dev ap0 station dump", shell=True).decode('utf-8').strip()

        for device in settings.get("TARGET_AP_MAC_ADDRESSES", []):
            if device["address"].lower() in output.lower():
                log.info("WiFi device %s (%s) connected to AP", device.get("name", "?"), device["address"])
                return True
        log.debug("No target WiFi devices connected to AP")
        return False
    except Exception as e:
        log.error("Error checking AP connected devices: %s", e)
        return False
