"""Tests for API authentication middleware and auth endpoints."""

import json
from unittest.mock import patch
from werkzeug.security import generate_password_hash


def _enable_auth(app, token="test-secret-token", password="test-password"):
    """Enable auth and set a known token + password in the test settings."""
    import modules.settings_helpers as sh
    import modules.auth as auth_mod
    with open(sh.SETTINGS_FILE, "r") as f:
        settings = json.load(f)
    settings["Auth"] = {
        "enabled": True,
        "token": token,
        "password_hash": generate_password_hash(password),
    }
    with open(sh.SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
    auth_mod.refresh()


def _disable_auth(app):
    """Disable auth in the test settings."""
    import modules.settings_helpers as sh
    import modules.auth as auth_mod
    with open(sh.SETTINGS_FILE, "r") as f:
        settings = json.load(f)
    auth = settings.get("Auth", {})
    settings["Auth"] = {
        "enabled": False,
        "token": auth.get("token", ""),
        "password_hash": auth.get("password_hash", ""),
    }
    with open(sh.SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
    auth_mod.refresh()


# --- Auth disabled (default) ---


def test_auth_disabled_allows_all(client):
    """When auth is disabled, endpoints work without a token."""
    res = client.get("/settings")
    assert res.status_code == 200


def test_auth_status_when_disabled(client):
    """GET /auth/status reports enabled=false."""
    res = client.get("/auth/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data["enabled"] is False


# --- Auth enabled ---


def test_401_without_token(app, client):
    """When auth is enabled, requests without token get 401."""
    _enable_auth(app)
    res = client.get("/settings")
    assert res.status_code == 401
    data = res.get_json()
    assert data["error"] == "Unauthorized"


def test_valid_bearer_header(app, client):
    """Valid Bearer token in header allows access."""
    _enable_auth(app, "my-secret")
    res = client.get("/settings", headers={"Authorization": "Bearer my-secret"})
    assert res.status_code == 200


def test_valid_query_param(app, client):
    """Valid token as query param allows access (for SSE)."""
    _enable_auth(app, "my-secret")
    res = client.get("/settings?token=my-secret")
    assert res.status_code == 200


def test_invalid_token_401(app, client):
    """Wrong token gets 401."""
    _enable_auth(app, "correct-token")
    res = client.get("/settings", headers={"Authorization": "Bearer wrong-token"})
    assert res.status_code == 401


def test_invalid_query_param_401(app, client):
    """Wrong token as query param gets 401."""
    _enable_auth(app, "correct-token")
    res = client.get("/settings?token=wrong-token")
    assert res.status_code == 401


# --- Exempt endpoints ---


def test_auth_status_exempt(app, client):
    """/auth/status is accessible without a token even when auth is enabled."""
    _enable_auth(app)
    res = client.get("/auth/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data["enabled"] is True


def test_auth_validate_exempt(app, client):
    """/auth/validate is accessible without a token (it's the login endpoint)."""
    _enable_auth(app, "my-api-token", "my-secret")
    res = client.post("/auth/validate",
                      json={"password": "my-secret"},
                      content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["valid"] is True
    assert data["token"] == "my-api-token"


def test_auth_validate_rejects_bad_password(app, client):
    """/auth/validate returns valid=false for wrong password."""
    _enable_auth(app, password="my-secret")
    res = client.post("/auth/validate",
                      json={"password": "wrong"},
                      content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["valid"] is False
    assert "token" not in data


# --- Token generation ---


def test_token_generated_when_empty(app):
    """When Auth.token is empty and refresh is called, regenerate_token fills it."""
    import modules.settings_helpers as sh
    import modules.auth as auth_mod
    with open(sh.SETTINGS_FILE, "r") as f:
        settings = json.load(f)
    settings["Auth"] = {"enabled": True, "token": "", "password_hash": ""}
    with open(sh.SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
    # Simulate what ensure_token does: if token is empty, generate one
    new_token = auth_mod.regenerate_token()
    assert len(new_token) > 20
    assert auth_mod.get_token() == new_token


# --- Token regeneration ---


def test_regenerate_token(app, client):
    """POST /auth/regenerate returns a new token."""
    _enable_auth(app, "old-token")
    res = client.post("/auth/regenerate",
                      headers={"Authorization": "Bearer old-token"})
    assert res.status_code == 200
    data = res.get_json()
    new_token = data["token"]
    assert new_token != "old-token"
    assert len(new_token) > 20

    # Old token should no longer work
    import modules.auth as auth_mod
    assert auth_mod.validate_token("old-token") is False
    assert auth_mod.validate_token(new_token) is True


# --- Auth status with token validation ---


def test_auth_status_validates_provided_token(app, client):
    """/auth/status returns valid=true when correct token is in header."""
    _enable_auth(app, "my-secret")
    res = client.get("/auth/status",
                     headers={"Authorization": "Bearer my-secret"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["enabled"] is True
    assert data["valid"] is True


def test_auth_status_invalid_token(app, client):
    """/auth/status returns valid=false when wrong token is provided."""
    _enable_auth(app, "my-secret")
    res = client.get("/auth/status",
                     headers={"Authorization": "Bearer wrong"})
    data = res.get_json()
    assert data["valid"] is False


# --- Settings update refreshes auth ---


def test_settings_update_refreshes_auth(app, client):
    """Updating Auth in settings refreshes the auth module."""
    _disable_auth(app)
    # Should work without auth
    res = client.get("/settings")
    assert res.status_code == 200

    # Enable auth via settings endpoint
    res = client.post("/settings",
                      json={"Auth": {"enabled": True, "token": "new-token"}},
                      content_type="application/json")
    assert res.status_code == 200

    # Now should require auth
    res = client.get("/settings")
    assert res.status_code == 401

    # Should work with the new token
    res = client.get("/settings",
                     headers={"Authorization": "Bearer new-token"})
    assert res.status_code == 200


# --- Password change ---


def test_set_password(app, client):
    """POST /auth/set-password changes the password."""
    _enable_auth(app, token="t", password="old-pass")
    res = client.post("/auth/set-password",
                      json={"current": "old-pass", "new": "new-pass"},
                      headers={"Authorization": "Bearer t"},
                      content_type="application/json")
    assert res.status_code == 200

    # Verify new password works
    import modules.auth as auth_mod
    assert auth_mod.validate_password("new-pass") is True
    assert auth_mod.validate_password("old-pass") is False


def test_set_password_wrong_current(app, client):
    """Changing password with wrong current password returns 403."""
    _enable_auth(app, token="t", password="real-pass")
    res = client.post("/auth/set-password",
                      json={"current": "wrong", "new": "new-pass"},
                      headers={"Authorization": "Bearer t"},
                      content_type="application/json")
    assert res.status_code == 403


def test_set_password_too_short(app, client):
    """Changing password to something too short returns 400."""
    _enable_auth(app, token="t", password="real-pass")
    res = client.post("/auth/set-password",
                      json={"current": "real-pass", "new": "ab"},
                      headers={"Authorization": "Bearer t"},
                      content_type="application/json")
    assert res.status_code == 400


def test_set_password_too_long(app, client):
    """Changing password to something over 128 chars returns 400."""
    _enable_auth(app, token="t", password="real-pass")
    res = client.post("/auth/set-password",
                      json={"current": "real-pass", "new": "x" * 129},
                      headers={"Authorization": "Bearer t"},
                      content_type="application/json")
    assert res.status_code == 400


def test_set_password_requires_auth(app, client):
    """/auth/set-password requires a valid token (not exempt)."""
    _enable_auth(app, token="t", password="pass")
    res = client.post("/auth/set-password",
                      json={"current": "pass", "new": "newpass"},
                      content_type="application/json")
    assert res.status_code == 401
