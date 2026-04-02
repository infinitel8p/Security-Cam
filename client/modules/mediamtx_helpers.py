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

# ISP image-quality keys (hardware ISP — zero CPU cost)
ISP_KEYS = {
    "brightness":  "rpiCameraBrightness",
    "contrast":    "rpiCameraContrast",
    "saturation":  "rpiCameraSaturation",
    "sharpness":   "rpiCameraSharpness",
    "ev":          "rpiCameraEV",
    "awb":         "rpiCameraAWB",
    "exposure":    "rpiCameraExposure",
    "denoise":     "rpiCameraDenoise",
    "metering":    "rpiCameraMetering",
}

# ISP defaults (match mediamtx.default.yml)
ISP_DEFAULTS = {
    "brightness": 0, "contrast": 1, "saturation": 1, "sharpness": 1,
    "ev": 0, "awb": "auto", "exposure": "normal", "denoise": "off",
    "metering": "centre",
}

# Valid enum values for ISP string params
_ISP_ENUMS = {
    "awb": {"auto", "incandescent", "tungsten", "fluorescent",
            "indoor", "daylight", "cloudy"},
    "exposure": {"normal", "short", "long"},
    "denoise": {"off", "cdn_fast", "cdn_hq"},
    "metering": {"centre", "spot", "matrix"},
}

# Numeric ranges for ISP slider params: key → (min, max)
_ISP_RANGES = {
    "brightness": (-1, 1),
    "contrast":   (0, 16),
    "saturation": (0, 16),
    "sharpness":  (0, 16),
    "ev":         (-10, 10),
}


def ensure_config() -> None:
    """Create mediamtx.yml from defaults if missing, merge new keys if stale.

    Same pattern as settings_helpers._ensure_settings(): the default file
    is tracked in git, the runtime file is gitignored.  On deploy the
    default may gain new keys - this merges them into the runtime config
    while preserving user customisations.
    """
    import shutil

    if not os.path.exists(DEFAULT_CONFIG_PATH):
        return

    if not os.path.exists(CONFIG_PATH):
        shutil.copy2(DEFAULT_CONFIG_PATH, CONFIG_PATH)
        log.info("Created mediamtx.yml from defaults")
        return

    # Merge: add keys present in default but missing in runtime
    with open(DEFAULT_CONFIG_PATH, "r") as f:
        default_cfg = yaml.safe_load(f) or {}
    with open(CONFIG_PATH, "r") as f:
        runtime_cfg = yaml.safe_load(f) or {}

    default_cam = default_cfg.get("paths", {}).get("cam", {})
    runtime_cam = runtime_cfg.get("paths", {}).get("cam", {})

    new_keys = {k: v for k, v in default_cam.items() if k not in runtime_cam}
    if new_keys:
        _patch_cam_values(new_keys)
        log.info("Merged %d new default key(s) into mediamtx.yml: %s",
                 len(new_keys), ", ".join(new_keys))


def read_config():
    """Read mediamtx.yml and return the cam path's rpiCamera params."""
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    cam = cfg.get("paths", {}).get("cam", {})
    result = {
        "width": cam.get("rpiCameraWidth", 1296),
        "height": cam.get("rpiCameraHeight", 972),
        "fps": cam.get("rpiCameraFPS", 30),
        "hflip": cam.get("rpiCameraHFlip", False),
        "vflip": cam.get("rpiCameraVFlip", False),
    }
    # ISP image-quality params
    for key, yml_key in ISP_KEYS.items():
        result[key] = cam.get(yml_key, ISP_DEFAULTS[key])
    return result


def _format_yaml_val(val) -> str:
    """Format a Python value for inline YAML output."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, str):
        return f"'{val}'"
    return str(val)


def _patch_cam_values(overrides: dict) -> None:
    """Patch key: value pairs in the paths.cam section of mediamtx.yml.

    Uses line-level replacement to preserve the original YAML formatting
    (MediaMTX is sensitive to flow vs block style for lists).
    Appends keys that don't already exist in the file.
    """
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()

    remaining = dict(overrides)
    cam_end_idx = None
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
            if stripped:
                cam_end_idx = i
            for key, val in list(remaining.items()):
                prefix = f"    {key}: "
                if stripped.startswith(prefix) or stripped == f"    {key}:":
                    lines[i] = f"    {key}: {_format_yaml_val(val)}\n"
                    del remaining[key]
                    break

    if remaining and cam_end_idx is not None:
        insert_at = cam_end_idx + 1
        for key, val in remaining.items():
            lines.insert(insert_at, f"    {key}: {_format_yaml_val(val)}\n")
            insert_at += 1

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


def update_isp_params(params):
    """Update rpiCamera ISP image-quality params and restart MediaMTX.

    params may contain any subset of ISP_KEYS.
    Returns (success: bool, error: str | None).
    """
    overrides = {}

    for key, yml_key in ISP_KEYS.items():
        if key not in params:
            continue
        val = params[key]

        # Validate enum params
        if key in _ISP_ENUMS:
            if val not in _ISP_ENUMS[key]:
                return False, f"Invalid {key}: {val!r}. Allowed: {sorted(_ISP_ENUMS[key])}"
            overrides[yml_key] = val

        # Validate numeric params
        elif key in _ISP_RANGES:
            try:
                val = float(val)
            except (TypeError, ValueError):
                return False, f"Invalid {key}: must be a number"
            lo, hi = _ISP_RANGES[key]
            if not (lo <= val <= hi):
                return False, f"Invalid {key}: must be between {lo} and {hi}"
            # Use int if the value is whole
            overrides[yml_key] = int(val) if val == int(val) else round(val, 2)

        log.info("ISP param %s → %s", yml_key, overrides.get(yml_key, val))

    if not overrides:
        return False, "No valid ISP parameters provided"

    _patch_cam_values(overrides)
    log.info("ISP config written, restarting MediaMTX...")
    return restart_service()


def sync_settings_to_config(settings: dict) -> None:
    """Apply persisted settings to mediamtx.yml (single patch, no restart).

    Called on startup after ensure_config() so mediamtx.yml exists.
    Applies user's rotation, resolution, and ISP settings from
    settings.json on top of the config.
    """
    if not os.path.exists(CONFIG_PATH):
        return

    overrides = {}

    # Stream resolution / FPS
    for key, yml_key in STREAM_KEYS.items():
        settings_key = {"width": "StreamWidth", "height": "StreamHeight",
                        "fps": "StreamFPS"}.get(key)
        if settings_key and settings_key in settings:
            overrides[yml_key] = int(settings[settings_key])

    # Stream-mode rotation (hflip/vflip)
    if settings.get("RotationMode") == "stream":
        angle = int(settings.get("RotationAngle", 0))
        if angle == 180:
            overrides["rpiCameraHFlip"] = True
            overrides["rpiCameraVFlip"] = True
        else:
            overrides["rpiCameraHFlip"] = False
            overrides["rpiCameraVFlip"] = False

    # ISP image-quality params
    isp = settings.get("ISP", {})
    for key, yml_key in ISP_KEYS.items():
        if key in isp:
            overrides[yml_key] = isp[key]

    if overrides:
        _patch_cam_values(overrides)
        log.info("Synced %d setting(s) to mediamtx.yml", len(overrides))


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
    # ISP image-quality params
    "rpiCameraBrightness", "rpiCameraContrast", "rpiCameraSaturation",
    "rpiCameraSharpness", "rpiCameraEV", "rpiCameraAWB",
    "rpiCameraExposure", "rpiCameraMetering",
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

    # Patch user camera values into the copied default.
    # Replace existing lines in-place; append any keys not present in the default
    # at the end of the cam section.
    with open(CONFIG_PATH, "r") as f:
        lines = f.readlines()

    remaining = dict(overrides)  # Track which keys still need inserting
    cam_end_idx = None  # Last line index inside the cam section
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
            if stripped:
                cam_end_idx = i
            for key, val in list(remaining.items()):
                prefix = f"    {key}: "
                if stripped.startswith(prefix) or stripped == f"    {key}:":
                    lines[i] = f"    {key}: {_format_yaml_val(val)}\n"
                    del remaining[key]
                    break

    # Append keys that weren't in the default file (e.g. rpiCameraHFlip)
    if remaining and cam_end_idx is not None:
        insert_at = cam_end_idx + 1
        for key, val in remaining.items():
            lines.insert(insert_at, f"    {key}: {_format_yaml_val(val)}\n")
            insert_at += 1

    with open(CONFIG_PATH, "w") as f:
        f.writelines(lines)
    log.info("MediaMTX config synced (defaults + %d user camera overrides)", len(overrides))
