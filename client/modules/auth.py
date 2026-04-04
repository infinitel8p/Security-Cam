"""Password-based dashboard authentication with API token access.

A single password protects the dashboard. On successful login the backend
returns an API token which the frontend stores and uses for all requests.
The API token can also be used directly for scripts and curl.
Auth can be disabled in settings for isolated network setups.
"""

import hmac
import logging
import secrets
import string

from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from modules import settings_helpers

log = logging.getLogger("auth")

# Cached state - refreshed on settings change
_token: str = ""
_enabled: bool = False
_password_hash: str = ""

EXEMPT_PATHS = frozenset([
    "/auth/status",
    "/auth/validate",
])


def _generate_password(length: int = 12) -> str:
    """Generate a random alphanumeric password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def ensure_token() -> None:
    """Generate a token and default password on first run if missing.

    Call once at startup.
    """
    global _token, _enabled, _password_hash
    settings = settings_helpers.get_settings()
    auth = settings.get("Auth", {})
    _enabled = auth.get("enabled", False)
    _token = auth.get("token", "")
    _password_hash = auth.get("password_hash", "")

    changed = False

    if not _token:
        _token = secrets.token_urlsafe(32)
        auth["token"] = _token
        changed = True
        log.info("Generated new API token: %s", _token)

    if not _password_hash:
        password = _generate_password()
        _password_hash = generate_password_hash(password)
        auth["password_hash"] = _password_hash
        changed = True
        log.info("Generated default password: %s", password)

    if changed:
        settings_helpers.update_settings({"Auth": {**auth}})


def refresh() -> None:
    """Re-read auth settings from disk. Call after settings change."""
    global _token, _enabled, _password_hash
    settings = settings_helpers.get_settings()
    auth = settings.get("Auth", {})
    _enabled = auth.get("enabled", False)
    _token = auth.get("token", "")
    _password_hash = auth.get("password_hash", "")


def is_enabled() -> bool:
    return _enabled


def get_token() -> str:
    return _token


def validate_token(token: str) -> bool:
    """Timing-safe token comparison."""
    if not _token:
        return False
    return hmac.compare_digest(token, _token)


def validate_password(password: str) -> bool:
    """Check a plaintext password against the stored hash."""
    if not _password_hash or not password:
        return False
    return check_password_hash(_password_hash, password)


def set_password(new_password: str) -> None:
    """Hash and store a new password."""
    global _password_hash
    _password_hash = generate_password_hash(new_password)
    settings = settings_helpers.get_settings()
    auth = settings.get("Auth", {})
    settings_helpers.update_settings({
        "Auth": {**auth, "password_hash": _password_hash}
    })
    log.info("Password updated")


def regenerate_token() -> str:
    """Generate a new token and persist it."""
    global _token
    _token = secrets.token_urlsafe(32)
    settings = settings_helpers.get_settings()
    auth = settings.get("Auth", {})
    settings_helpers.update_settings({
        "Auth": {**auth, "token": _token}
    })
    log.info("API token regenerated")
    return _token


def check_request() -> bool:
    """Check if the current request is authorized. Returns True if allowed."""
    if not _enabled:
        return True
    if request.path in EXEMPT_PATHS:
        return True

    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if validate_token(token):
            return True

    # Check query param (for SSE / EventSource)
    token = request.args.get("token", "")
    if token and validate_token(token):
        return True

    return False
