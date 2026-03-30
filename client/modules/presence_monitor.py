import logging
import threading
import time

from . import activity_helpers
from . import event_logger
from . import settings_helpers

log = logging.getLogger("presence")

POLL_INTERVAL = 30  # seconds

_thread = None
# Track last-known state: {"AA:BB:CC:DD:EE:FF": True/False}
_bt_state: dict[str, bool] = {}
_wifi_state: dict[str, bool] = {}


def _device_name(address: str, device_list: list[dict]) -> str:
    """Look up the friendly name for a device address."""
    for d in device_list:
        if d["address"].upper() == address.upper():
            return d.get("name") or address
    return address


def _check_presence():
    """Poll device statuses and log arrive/leave transitions."""
    global _bt_state, _wifi_state

    settings = settings_helpers.get_settings()
    bt_devices = settings.get("TARGET_BT_ADDRESSES", [])
    wifi_devices = settings.get("TARGET_AP_MAC_ADDRESSES", [])

    statuses = activity_helpers.get_device_statuses()

    # Check Bluetooth transitions
    for addr, online in statuses["bt"].items():
        was_online = _bt_state.get(addr)
        if was_online is not None and online != was_online:
            name = _device_name(addr, bt_devices)
            if online:
                log.info("BT device arrived: %s (%s)", name, addr)
                event_logger.log_event("device_arrived", f"{name} (Bluetooth)")
            else:
                log.info("BT device left: %s (%s)", name, addr)
                event_logger.log_event("device_left", f"{name} (Bluetooth)")
        _bt_state[addr] = online

    # Check WiFi transitions
    for addr, online in statuses["wifi"].items():
        was_online = _wifi_state.get(addr)
        if was_online is not None and online != was_online:
            name = _device_name(addr, wifi_devices)
            if online:
                log.info("WiFi device arrived: %s (%s)", name, addr)
                event_logger.log_event("device_arrived", f"{name} (WiFi)")
            else:
                log.info("WiFi device left: %s (%s)", name, addr)
                event_logger.log_event("device_left", f"{name} (WiFi)")
        _wifi_state[addr] = online

    # Clean up stale entries (devices removed from settings)
    current_bt = set(statuses["bt"].keys())
    current_wifi = set(statuses["wifi"].keys())
    _bt_state = {k: v for k, v in _bt_state.items() if k in current_bt}
    _wifi_state = {k: v for k, v in _wifi_state.items() if k in current_wifi}


def _monitor_loop():
    """Background loop that checks presence at regular intervals."""
    while True:
        try:
            _check_presence()
        except Exception as e:
            log.error("Presence monitor error: %s", e)
        time.sleep(POLL_INTERVAL)


def start():
    """Start the background presence monitor thread."""
    global _thread
    if _thread is not None:
        return
    _thread = threading.Thread(target=_monitor_loop, daemon=True)
    _thread.start()
    log.info("Presence monitor started (%ds intervals)", POLL_INTERVAL)
