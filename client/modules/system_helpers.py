import subprocess
import psutil


def get_uptime():
    """
    Returns system uptime in seconds.

    Returns:
        int: Uptime in seconds since last boot.
    """
    import time
    return round(time.time() - psutil.boot_time())


def get_throttle_status():
    """
    Returns Raspberry Pi throttle status from vcgencmd.

    Returns:
        dict | None: Throttle flags, or None if not running on a Pi.
    """
    try:
        result = subprocess.run(
            ["vcgencmd", "get_throttled"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None

        # Output is "throttled=0x50000" or similar
        hex_str = result.stdout.strip().split("=")[-1]
        flags = int(hex_str, 16)

        return {
            "raw": hex_str,
            "under_voltage_now": bool(flags & 0x1),
            "freq_capped_now": bool(flags & 0x2),
            "throttled_now": bool(flags & 0x4),
            "soft_temp_limit_now": bool(flags & 0x8),
            "under_voltage_occurred": bool(flags & 0x10000),
            "freq_capped_occurred": bool(flags & 0x20000),
            "throttled_occurred": bool(flags & 0x40000),
            "soft_temp_limit_occurred": bool(flags & 0x80000),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
        return None


def get_sd_health():
    """
    Returns SD card health info from /sys/block/mmcblk0.

    Returns:
        dict | None: SD card info, or None if not available.
    """
    import os

    base = "/sys/block/mmcblk0"
    if not os.path.isdir(base):
        return None

    def _read(path):
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            return None

    device = base + "/device"
    info = {}

    # Card identification
    name = _read(f"{device}/name")
    if name:
        info["name"] = name
    oemid = _read(f"{device}/oemid")
    if oemid:
        info["oemid"] = oemid
    serial = _read(f"{device}/serial")
    if serial:
        info["serial"] = serial
    mfg_date = _read(f"{device}/date")
    if mfg_date:
        info["manufacturing_date"] = mfg_date
    hw_rev = _read(f"{device}/hwrev")
    if hw_rev:
        info["hw_revision"] = hw_rev
    fw_rev = _read(f"{device}/fwrev")
    if fw_rev:
        info["fw_revision"] = fw_rev

    # Life time estimation (eMMC / some SD cards)
    life_a = _read(f"{device}/life_time")
    if life_a:
        info["life_time_est"] = life_a

    # Preferred erase size — can hint at wear leveling block size
    pref_erase = _read(f"{device}/preferred_erase_size")
    if pref_erase:
        try:
            info["preferred_erase_size_mb"] = int(pref_erase) // (1024 * 1024)
        except ValueError:
            pass

    # Bytes written since boot (sum all mmcblk0* partitions from diskstats)
    try:
        total_sectors = 0
        with open("/proc/diskstats", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 10 and parts[2].startswith("mmcblk0"):
                    # parts[9] = sectors written (512 bytes each)
                    total_sectors += int(parts[9])
        if total_sectors > 0:
            info["written_since_boot_gb"] = round(
                total_sectors * 512 / (1024 ** 3), 2
            )
    except (FileNotFoundError, PermissionError, ValueError):
        pass

    return info if info else None


def get_cpu_temp():
    """
    Returns the CPU temperature of the Raspberry Pi.

    Returns:
        int: The CPU temperature in Celsius rounded to the nearest integer.
        None: If the temperature file is not found.
    """
    
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temp_str = file.read().strip()
            cpu_temp = int(temp_str) / 1000.0
            return round(cpu_temp)
    except FileNotFoundError:
        return None


def get_cpu_load():
    """
    Returns the CPU load as a percentage, considering the maximum load across all cores.

    Returns:
        int: The CPU load as a percentage rounded to the nearest integer.
    """
    
    per_core_loads = psutil.cpu_percent(interval=1, percpu=True)
    max_load = max(per_core_loads)
    return round(max_load)


def get_storage_info():
    """
    Returns the total size and used space of the disk where the root directory is mounted.

    Returns:
        dict[str, int]: A dictionary containing the total and used space in GB, each rounded to the nearest integer.
    """

    usage = psutil.disk_usage('/')
    total = usage.total / (1024 ** 3)  # Convert bytes to GB
    used = usage.used / (1024 ** 3)    # Convert bytes to GB
    return {'total_gb': round(total), 'used_gb': round(used)}


def get_ram_usage():
    """
    Returns the total and used RAM in MB.

    Returns:
        dict[str, int]: A dictionary containing the total and used RAM in MB, each rounded to the nearest integer.
    """

    mem = psutil.virtual_memory()
    total = mem.total / (1024 ** 2)  # Convert bytes to MB
    used = mem.used / (1024 ** 2)    # Convert bytes to MB
    return {'total_mb': round(total), 'used_mb': round(used)}
