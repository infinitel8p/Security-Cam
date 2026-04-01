import logging
import threading
import time

from . import activity_helpers
from . import event_logger
from . import settings_helpers
from . import sse

log = logging.getLogger("presence")

POLL_INTERVAL = 30  # seconds
EVENT_COOLDOWN = 120  # seconds - suppress duplicate events for the same device+type
MISS_THRESHOLD = 3  # consecutive missed polls before declaring a device "left"

_thread = None
_state_lock = threading.Lock()
# Track last-known state: {"AA:BB:CC:DD:EE:FF": True/False}
_bt_state: dict[str, bool] = {}
_wifi_state: dict[str, bool] = {}
# Miss counters for hysteresis (BT only — WiFi station list is authoritative)
_bt_miss_count: dict[str, int] = {}
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


def _emit_transition(addr: str, online: bool, name: str, transport: str,
                     state_dict: dict[str, bool]):
    """Log an arrive/leave event and update state. Caller must hold _state_lock."""
    event_type = "device_arrived" if online else "device_left"
    if _should_log(addr, event_type):
        label = "arrived" if online else "left"
        log.info("%s device %s: %s (%s)", transport, label, name, addr)
        event_logger.log_event(event_type, f"{name} ({transport})")
        sse.emit("presence_change", {
            "address": addr, "name": name,
            "transport": transport.lower(), "online": online,
        })
        state_dict[addr] = online


def _handle_bt_poll(addr: str, online: bool, name: str):
    """Process a BT poll result with hysteresis. Caller must hold _state_lock."""
    was_online = _bt_state.get(addr)

    if online:
        # Device responded — reset miss counter, handle arrival
        _bt_miss_count[addr] = 0
        if was_online is None:
            # First time seeing this device after boot
            _bt_state[addr] = True
            log.info("Bluetooth device already present at startup: %s (%s)", name, addr)
            event_logger.log_event("device_arrived", f"{name} (Bluetooth)")
        elif not was_online:
            _emit_transition(addr, True, name, "Bluetooth", _bt_state)
    else:
        # Device not found — increment miss counter
        count = _bt_miss_count.get(addr, 0) + 1
        _bt_miss_count[addr] = count

        if was_online is None:
            # First poll after boot, device not found — just set state silently
            _bt_state[addr] = False
            return

        if was_online and count >= MISS_THRESHOLD:
            # Enough consecutive misses — declare "left"
            log.info("Bluetooth device missed %d consecutive polls: %s (%s)",
                     count, name, addr)
            _emit_transition(addr, False, name, "Bluetooth", _bt_state)
        elif was_online:
            log.debug("Bluetooth device missed poll %d/%d: %s (%s)",
                      count, MISS_THRESHOLD, name, addr)


def _handle_wifi_transition(addr: str, online: bool, name: str):
    """Process a WiFi state change (no hysteresis needed). Caller must hold _state_lock."""
    was_online = _wifi_state.get(addr)

    if was_online is None:
        _wifi_state[addr] = online
        if online:
            log.info("WiFi device already present at startup: %s (%s)", name, addr)
            event_logger.log_event("device_arrived", f"{name} (WiFi)")
        return

    if online != was_online:
        _emit_transition(addr, online, name, "WiFi", _wifi_state)


def report_bt_status(addr: str, online: bool):
    """Push an externally-observed BT status into the presence monitor.

    Called by the sensor manager after its own BT lookup so the activity
    timeline stays in sync without waiting for the next poll cycle.
    """
    addr = addr.upper()
    with _state_lock:
        if online:
            _bt_miss_count[addr] = 0
            if _bt_state.get(addr) is False:
                settings = settings_helpers.get_settings()
                bt_devices = settings.get("TARGET_BT_ADDRESSES", [])
                name = _device_name(addr, bt_devices)
                _emit_transition(addr, True, name, "Bluetooth", _bt_state)
        else:
            count = _bt_miss_count.get(addr, 0) + 1
            _bt_miss_count[addr] = count
            if _bt_state.get(addr) is True and count >= MISS_THRESHOLD:
                settings = settings_helpers.get_settings()
                bt_devices = settings.get("TARGET_BT_ADDRESSES", [])
                name = _device_name(addr, bt_devices)
                _emit_transition(addr, False, name, "Bluetooth", _bt_state)


def _check_presence():
    """Poll device statuses and log arrive/leave transitions."""
    global _bt_state, _wifi_state, _bt_miss_count

    settings = settings_helpers.get_settings()
    bt_devices = settings.get("TARGET_BT_ADDRESSES", [])
    wifi_devices = settings.get("TARGET_AP_MAC_ADDRESSES", [])

    statuses = activity_helpers.get_device_statuses()

    with _state_lock:
        for addr, online in statuses["bt"].items():
            name = _device_name(addr, bt_devices)
            _handle_bt_poll(addr, online, name)

        for addr, online in statuses["wifi"].items():
            name = _device_name(addr, wifi_devices)
            _handle_wifi_transition(addr, online, name)

        # Clean up stale entries (devices removed from settings)
        current_bt = set(statuses["bt"].keys())
        current_wifi = set(statuses["wifi"].keys())
        _bt_state = {k: v for k, v in _bt_state.items() if k in current_bt}
        _wifi_state = {k: v for k, v in _wifi_state.items() if k in current_wifi}
        _bt_miss_count = {k: v for k, v in _bt_miss_count.items() if k in current_bt}

    # Push connection summary to SSE clients
    bt_online = sum(1 for v in statuses["bt"].values() if v)
    wifi_online = sum(1 for v in statuses["wifi"].values() if v)
    ap_clients = len(activity_helpers.get_ap_stations()) if activity_helpers.is_in_ap_mode() else 0
    sse.emit("connections", {
        "bluetooth": {"online": bt_online, "total": len(statuses["bt"])},
        "wifi": {"online": wifi_online, "total": len(statuses["wifi"])},
        "ap_clients": ap_clients,
    })


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
    log.info("Presence monitor started (%ds intervals, %d miss threshold)",
             POLL_INTERVAL, MISS_THRESHOLD)
