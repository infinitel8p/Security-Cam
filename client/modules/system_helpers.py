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
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


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
