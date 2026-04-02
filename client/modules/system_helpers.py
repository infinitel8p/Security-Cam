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


_static_cache: dict | None = None


def _get_static_info() -> dict:
    """Return platform info that never changes at runtime (cached once)."""
    global _static_cache
    if _static_cache is not None:
        return _static_cache

    import getpass
    import platform
    import shutil

    info: dict = {}
    try:
        info["username"] = getpass.getuser()
    except Exception:
        pass
    info["python_version"] = platform.python_version()
    info["os_info"] = platform.platform()
    info["arch"] = platform.machine()
    info["kernel"] = platform.release()

    # Distro info from /etc/os-release
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    info["os_distro"] = line.split("=", 1)[1].strip().strip('"')
                    break
    except (FileNotFoundError, PermissionError):
        pass

    # CPU model
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    info["cpu_model"] = line.split(":", 1)[1].strip()
                    break
            else:
                f.seek(0)
                for line in f:
                    if line.lower().startswith("hardware"):
                        info["cpu_model"] = line.split(":", 1)[1].strip()
                        break
    except (FileNotFoundError, PermissionError):
        proc = platform.processor()
        if proc:
            info["cpu_model"] = proc

    # Flask version
    import flask
    info["flask_version"] = flask.__version__
    try:
        import cv2
        info["opencv_version"] = cv2.__version__
    except Exception:
        pass

    # Node.js version
    node_bin = shutil.which("node")
    if node_bin:
        try:
            result = subprocess.run(
                [node_bin, "--version"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                info["node_version"] = result.stdout.strip().lstrip("v")
        except Exception:
            pass

    # MediaMTX version
    mtx_bin = shutil.which("mediamtx") or "/usr/local/bin/mediamtx"
    try:
        result = subprocess.run(
            [mtx_bin, "--version"],
            capture_output=True, text=True, timeout=2,
        )
        out = (result.stdout or result.stderr).strip()
        if result.returncode == 0 and out:
            info["mediamtx_version"] = out.split()[-1] if " " in out else out
    except Exception:
        pass

    _static_cache = info
    return _static_cache


def get_extended_stats():
    """
    Returns additional system stats: process count, network I/O,
    swap usage, CPU core count, boot timestamp, and hostname.
    """
    import socket
    from datetime import datetime, timezone

    stats = {}

    # Process count
    stats["process_count"] = len(psutil.pids())

    # CPU cores
    stats["cpu_count"] = psutil.cpu_count(logical=True)

    # Per-core load
    per_core = psutil.cpu_percent(interval=0, percpu=True)
    stats["cpu_per_core"] = [round(c) for c in per_core]

    # Boot timestamp (ISO 8601)
    boot = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
    stats["boot_time"] = boot.isoformat()

    # Hostname
    stats["hostname"] = socket.gethostname()

    # Network I/O (bytes sent/received since boot)
    net = psutil.net_io_counters()
    if net:
        stats["network"] = {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        }

    # Swap
    swap = psutil.swap_memory()
    stats["swap"] = {
        "total_mb": round(swap.total / (1024 ** 2)),
        "used_mb": round(swap.used / (1024 ** 2)),
        "percent": round(swap.percent),
    }

    # Load averages (1, 5, 15 min)
    try:
        load1, load5, load15 = psutil.getloadavg()
        stats["load_avg"] = {
            "1min": round(load1, 2),
            "5min": round(load5, 2),
            "15min": round(load15, 2),
        }
    except (AttributeError, OSError):
        pass

    # Static platform info (cached — never changes at runtime)
    stats.update(_get_static_info())

    # Dynamic network info (can change if WiFi reconnects)
    try:
        addrs = psutil.net_if_addrs()
        for iface in ("wlan0", "wlan1", "eth0", "end0"):
            if iface in addrs:
                for addr in addrs[iface]:
                    if addr.family.name == "AF_INET" and not addr.address.startswith("127."):
                        stats["ip_address"] = addr.address
                        stats["ip_interface"] = iface
                        break
            if "ip_address" in stats:
                break
    except Exception:
        pass

    # WiFi SSID (dynamic — can change on reconnect)
    import shutil
    if shutil.which("iw"):
        try:
            result = subprocess.run(
                ["iw", "dev", "wlan0", "link"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("SSID:"):
                        stats["wifi_ssid"] = line.split(":", 1)[1].strip()
                    elif line.startswith("signal:"):
                        try:
                            stats["wifi_signal_dbm"] = int(line.split(":", 1)[1].strip().split()[0])
                        except (ValueError, IndexError):
                            pass
        except Exception:
            pass

        # AP client signal strengths (when Pi is running as access point)
        try:
            result = subprocess.run(
                ["iw", "dev", "ap0", "station", "dump"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                ap_clients = []
                current_mac = None
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("Station "):
                        current_mac = line.split()[1]
                    elif line.startswith("signal:") and current_mac:
                        try:
                            dbm = int(line.split(":", 1)[1].strip().split()[0])
                            ap_clients.append({"mac": current_mac, "signal_dbm": dbm})
                        except (ValueError, IndexError):
                            pass
                if ap_clients:
                    stats["ap_clients_signal"] = ap_clients
        except Exception:
            pass

    return stats
