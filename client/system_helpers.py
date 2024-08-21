import psutil


def get_cpu_temp() -> float | None:
    """
    Returns the CPU temperature of the Raspberry Pi.

    Returns:
        float: The CPU temperature in Celsius.
        None: If the temperature file is not found.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temp_str = file.read().strip()
            cpu_temp = int(temp_str) / 1000.0
            return cpu_temp
    except FileNotFoundError:
        return None


def get_cpu_load() -> float:
    """
    Returns the CPU load as a percentage.

    Returns:
        float: The CPU load as a percentage.
    """
    return psutil.cpu_percent(interval=1)


def get_storage_info() -> dict[str, float]:
    """
    Returns the total size and used space of the disk where the root directory is mounted.

    Returns:
        dict[str, float]: A dictionary containing the total and used space in GB.
    """
    usage = psutil.disk_usage('/')
    total = usage.total / (1024 ** 3)  # Convert bytes to GB
    used = usage.used / (1024 ** 3)    # Convert bytes to GB
    return {'total_gb': total, 'used_gb': used}


def get_ram_usage() -> dict[str, float]:
    """
    Returns the total and used RAM in MB.

    Returns:
        dict[str, float]: A dictionary containing the total and used RAM in MB.
    """
    mem = psutil.virtual_memory()
    total = mem.total / (1024 ** 2)  # Convert bytes to MB
    used = mem.used / (1024 ** 2)    # Convert bytes to MB
    return {'total_mb': total, 'used_mb': used}
