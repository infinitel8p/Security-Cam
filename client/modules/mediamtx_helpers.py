import logging
import os
import subprocess
import yaml

log = logging.getLogger("stream.mtx")

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "data",
)
CONFIG_PATH = os.path.join(_DATA_DIR, "mediamtx.yml")
DEFAULT_CONFIG_PATH = os.path.join(_DATA_DIR, "mediamtx.default.yml")

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
            ["systemctl", "restart", "mediamtx"],
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


# Keys under paths.cam that belong to the user (preserved across updates)
_USER_CAM_KEYS = {
    "rpiCameraWidth", "rpiCameraHeight", "rpiCameraFPS",
    "rpiCameraBitrate", "rpiCameraCodec", "rpiCameraIDRPeriod",
    "rpiCameraHFlip", "rpiCameraVFlip", "rpiCameraDenoise",
    "rpiCameraTextOverlayEnable", "rpiCameraTextOverlay",
}


def sync_config():
    """Merge upstream defaults with user's camera settings.

    Called during update to pick up new config keys (e.g. logDestinations)
    without overwriting the user's camera-specific tuning.
    """
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        log.warning("No default config at %s, skipping sync", DEFAULT_CONFIG_PATH)
        return

    with open(DEFAULT_CONFIG_PATH, "r") as f:
        defaults = yaml.safe_load(f)

    if not os.path.exists(CONFIG_PATH):
        log.info("No runtime config found, copying defaults")
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(defaults, f, default_flow_style=False, sort_keys=False)
        return

    with open(CONFIG_PATH, "r") as f:
        user_cfg = yaml.safe_load(f) or {}

    # Start from the upstream defaults
    merged = dict(defaults)

    # Preserve user's camera-specific settings
    user_cam = user_cfg.get("paths", {}).get("cam", {})
    if user_cam:
        merged_cam = merged.setdefault("paths", {}).setdefault("cam", {})
        for key in _USER_CAM_KEYS:
            if key in user_cam:
                merged_cam[key] = user_cam[key]

    with open(CONFIG_PATH, "w") as f:
        yaml.dump(merged, f, default_flow_style=False, sort_keys=False)
    log.info("MediaMTX config synced (defaults + user camera settings)")
