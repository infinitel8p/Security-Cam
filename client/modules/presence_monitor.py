import logging
import threading
import time

from . import activity_helpers
from . import event_logger
from . import settings_helpers

log = logging.getLogger("presence")

POLL_INTERVAL = 30  # seconds
EVENT_COOLDOWN = 120  # seconds — suppress duplicate events for the same device+type

_thread = None
# Track last-known state: {"AA:BB:CC:DD:EE:FF": True/False}
_bt_state: dict[str, bool] = {}
_wifi_state: dict[str, bool] = {}
# Track last event time per (address, event_type) to debounce flapping
_last_event: dict[tuple[str, str], float] = {}


def _device_name(address: str, device_list: list[dict]) -> str:
    """Look up the friendly name for a device address."""
    for d in device_list:
        if d["address"].upper() == address.upper():
            return d.get("name") or address
    return address


def _should_log(addr: str, event_type: str) -> bool:
    """Return True if enough time has passed since the last event for this device+type."""
    key = (addr.upper(), event_type)
    now = time.monotonic()
    last = _last_event.get(key, 0)
    if now - last < EVENT_COOLDOWN:
        return False
    _last_event[key] = now
    return True


def _handle_transition(addr: str, online: bool, name: str, transport: str,
                        state_dict: dict[str, bool]):
    """Process a single device state change with debounce.

    Only updates the tracked state when the event is actually logged (or on
    first sight).  If the cooldown suppresses the log, the state stays at the
    old value so the transition is re-evaluated on the next poll cycle — no
    events are silently lost.
    """
    was_online = state_dict.get(addr)

    # First time seeing this device — just record state, don't log
    if was_online is None:
        state_dict[addr] = online
        return

    # No change
    if online == was_online:
        return

    event_type = "device_arrived" if online else "device_left"
    if _should_log(addr, event_type):
        label = "arrived" if online else "left"
        log.info("%s device %s: %s (%s)", transport, label, name, addr)
        event_logger.log_event(event_type, f"{name} ({transport})")
        # Commit the state change only after a successful log
        state_dict[addr] = online
    # else: leave state_dict unchanged so we retry next poll


def _check_presence():
    """Poll device statuses and log arrive/leave transitions."""
    global _bt_state, _wifi_state

    settings = settings_helpers.get_settings()
    bt_devices = settings.get("TARGET_BT_ADDRESSES", [])
    wifi_devices = settings.get("TARGET_AP_MAC_ADDRESSES", [])

    statuses = activity_helpers.get_device_statuses()

    for addr, online in statuses["bt"].items():
        name = _device_name(addr, bt_devices)
        _handle_transition(addr, online, name, "Bluetooth", _bt_state)

    for addr, online in statuses["wifi"].items():
        name = _device_name(addr, wifi_devices)
        _handle_transition(addr, online, name, "WiFi", _wifi_state)

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
