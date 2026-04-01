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


def _patch_cam_values(overrides: dict) -> None:
    """Patch key: value pairs in the paths.cam section of mediamtx.yml.

    Uses line-level replacement to preserve the original YAML formatting
    (MediaMTX is sensitive to flow vs block style for lists).
    """
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()

    in_cam = False
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped == "  cam:":
            in_cam = True
            continue
        if in_cam:
            if stripped and not stripped.startswith("    "):
                in_cam = False
                continue
            for key, val in overrides.items():
                prefix = f"    {key}: "
                if stripped.startswith(prefix) or stripped == f"    {key}:":
                    if isinstance(val, bool):
                        yaml_val = "true" if val else "false"
                    elif isinstance(val, str):
                        yaml_val = f"'{val}'"
                    else:
                        yaml_val = str(val)
                    lines[i] = f"    {key}: {yaml_val}\n"
                    break

    with open(CONFIG_PATH, "w") as f:
        f.writelines(lines)


def update_stream_params(params):
    """Update rpiCamera stream params in mediamtx.yml and restart the service.

    params may contain: width, height, fps, rotation_angle (for stream mode).
    Returns (success: bool, error: str | None).
    """
    overrides = {}

    for key, yml_key in STREAM_KEYS.items():
        if key in params:
            overrides[yml_key] = int(params[key])
            log.info("MediaMTX param %s → %s", yml_key, params[key])

    # Handle stream-mode rotation (hflip/vflip)
    if "rotation_angle" in params:
        angle = int(params["rotation_angle"])
        if angle == 0:
            overrides["rpiCameraHFlip"] = False
            overrides["rpiCameraVFlip"] = False
        elif angle == 180:
            overrides["rpiCameraHFlip"] = True
            overrides["rpiCameraVFlip"] = True
        else:
            return False, f"Hardware rotation only supports 0° and 180°. Got {angle}°."

    _patch_cam_values(overrides)
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

    Strategy: copy the default file verbatim (preserving its original YAML
    formatting — MediaMTX is sensitive to flow vs block style), then patch
    user camera values back in via line-level replacements.  This avoids
    yaml.dump which would reformat the file and break MediaMTX parsing.
    """
    import shutil

    if not os.path.exists(DEFAULT_CONFIG_PATH):
        log.warning("No default config at %s, skipping sync", DEFAULT_CONFIG_PATH)
        return

    if not os.path.exists(CONFIG_PATH):
        log.info("No runtime config found, copying defaults")
        shutil.copy2(DEFAULT_CONFIG_PATH, CONFIG_PATH)
        return

    # Read user's current camera-specific values before overwriting
    with open(CONFIG_PATH, "r") as f:
        user_cfg = yaml.safe_load(f) or {}

    user_cam = user_cfg.get("paths", {}).get("cam", {})
    overrides = {}
    for key in _USER_CAM_KEYS:
        if key in user_cam:
            overrides[key] = user_cam[key]

    # Copy default file verbatim (preserves comments, flow-style lists, etc.)
    shutil.copy2(DEFAULT_CONFIG_PATH, CONFIG_PATH)

    if not overrides:
        log.info("MediaMTX config synced (defaults only, no user camera overrides)")
        return

    # Patch user camera values into the copied default via YAML load/dump.
    # We only modify paths.cam keys, then write back — but we must preserve
    # the original formatting.  Read the file as lines, do targeted
    # key: value replacements within the cam section.
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()

    in_cam = False
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        # Detect "  cam:" section start (2-space indent under paths:)
        if stripped == "  cam:":
            in_cam = True
            continue
        if in_cam:
            # End of cam section: line with <= 2-space indent (or less)
            if stripped and not stripped.startswith("    "):
                in_cam = False
                continue
            # Check if this line sets a key we want to override
            for key, val in overrides.items():
                prefix = f"    {key}: "
                if stripped.startswith(prefix) or stripped == f"    {key}:":
                    # Format the value appropriately
                    if isinstance(val, bool):
                        yaml_val = "true" if val else "false"
                    elif isinstance(val, str):
                        yaml_val = f"'{val}'"
                    else:
                        yaml_val = str(val)
                    lines[i] = f"    {key}: {yaml_val}\n"
                    break

    with open(CONFIG_PATH, "w") as f:
        f.writelines(lines)
    log.info("MediaMTX config synced (defaults + %d user camera overrides)", len(overrides))
