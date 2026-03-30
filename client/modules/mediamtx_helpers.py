import logging
import os
import subprocess
import yaml

log = logging.getLogger("mediamtx")

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "data", "mediamtx.yml"
)

# Keys we allow the dashboard to modify
STREAM_KEYS = {
    "width": "rpiCameraWidth",
    "height": "rpiCameraHeight",
    "fps": "rpiCameraFPS",
}


def read_config():
    """Read mediamtx.yml and return the cam path's rpiCamera params."""
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    cam = cfg.get("paths", {}).get("cam", {})
    return {
        "width": cam.get("rpiCameraWidth", 1296),
        "height": cam.get("rpiCameraHeight", 972),
        "fps": cam.get("rpiCameraFPS", 30),
        "hflip": cam.get("rpiCameraHFlip", False),
        "vflip": cam.get("rpiCameraVFlip", False),
    }


def update_stream_params(params):
    """Update rpiCamera stream params in mediamtx.yml and restart the service.

    params may contain: width, height, fps, rotation_angle (for stream mode).
    Returns (success: bool, error: str | None).
    """
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    cam = cfg.setdefault("paths", {}).setdefault("cam", {})

    for key, yml_key in STREAM_KEYS.items():
        if key in params:
            cam[yml_key] = int(params[key])
            log.info("MediaMTX param %s → %s", yml_key, params[key])

    # Handle stream-mode rotation (hflip/vflip)
    if "rotation_angle" in params:
        angle = int(params["rotation_angle"])
        if angle == 0:
            cam["rpiCameraHFlip"] = False
            cam["rpiCameraVFlip"] = False
        elif angle == 180:
            cam["rpiCameraHFlip"] = True
            cam["rpiCameraVFlip"] = True
        else:
            return False, f"Hardware rotation only supports 0° and 180°. Got {angle}°."

    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
    log.info("MediaMTX config written, restarting service...")

    return restart_service()


def restart_service():
    """Restart the mediamtx systemd service. Returns (success, error)."""
    try:
        subprocess.run(
            ["sudo", "systemctl", "restart", "mediamtx"],
            check=True, capture_output=True, timeout=10,
        )
        log.info("MediaMTX service restarted successfully")
        return True, None
    except subprocess.CalledProcessError as e:
        msg = f"Failed to restart MediaMTX: {e.stderr.decode().strip()}"
        log.error(msg)
        return False, msg
    except subprocess.TimeoutExpired:
        log.error("MediaMTX restart timed out")
        return False, "MediaMTX restart timed out"
    except FileNotFoundError:
        log.error("systemctl not found - not running on Pi?")
        return False, "systemctl not found (not running on the Pi?)"
