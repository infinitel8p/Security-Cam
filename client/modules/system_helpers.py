import psutil


def get_cpu_temp() -> int | None:
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


def get_cpu_load() -> int:
    """
    Returns the CPU load as a percentage, considering the maximum load across all cores.

    Returns:
        int: The CPU load as a percentage rounded to the nearest integer.
    """
    
    per_core_loads = psutil.cpu_percent(interval=1, percpu=True)
    max_load = max(per_core_loads)
    return round(max_load)


def get_storage_info() -> dict[str, int]:
    """
    Returns the total size and used space of the disk where the root directory is mounted.

    Returns:
        dict[str, int]: A dictionary containing the total and used space in GB, each rounded to the nearest integer.
    """

    usage = psutil.disk_usage('/')
    total = usage.total / (1024 ** 3)  # Convert bytes to GB
    used = usage.used / (1024 ** 3)    # Convert bytes to GB
    return {'total_gb': round(total), 'used_gb': round(used)}


def get_ram_usage() -> dict[str, int]:
    """
    Returns the total and used RAM in MB.

    Returns:
        dict[str, int]: A dictionary containing the total and used RAM in MB, each rounded to the nearest integer.
    """

    mem = psutil.virtual_memory()
    total = mem.total / (1024 ** 2)  # Convert bytes to MB
    used = mem.used / (1024 ** 2)    # Convert bytes to MB
    return {'total_mb': round(total), 'used_mb': round(used)}
