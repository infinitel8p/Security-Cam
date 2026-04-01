"""Tests for system alert evaluation and the /system_alert_state endpoint."""

from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# evaluate_alerts() unit tests
# ---------------------------------------------------------------------------

def _make_info(temp=45, load=30, throttle_active=False, storage_pct=50, sd_life=None):
    """Build a snapshot-like dict for evaluate_alerts()."""
    return {
        "temp": temp,
        "load": load,
        "throttle_active": throttle_active,
        "storage_pct": storage_pct,
        "sd_life_est": sd_life,
    }


def test_evaluate_alerts_all_ok():
    from modules.health_logger import evaluate_alerts
    alerts = evaluate_alerts(_make_info())
    assert alerts["cpu_temp"] == "ok"
    assert alerts["throttle"] == "ok"
    assert alerts["storage"] == "ok"


def test_evaluate_alerts_temp_warning():
    from modules.health_logger import evaluate_alerts
    alerts = evaluate_alerts(_make_info(temp=66))
    assert alerts["cpu_temp"] == "warn"


def test_evaluate_alerts_temp_critical():
    from modules.health_logger import evaluate_alerts
    alerts = evaluate_alerts(_make_info(temp=81))
    assert alerts["cpu_temp"] == "critical"


def test_evaluate_alerts_throttle_critical():
    from modules.health_logger import evaluate_alerts
    alerts = evaluate_alerts(_make_info(throttle_active=True))
    assert alerts["throttle"] == "critical"


def test_evaluate_alerts_storage_warning():
    from modules.health_logger import evaluate_alerts
    alerts = evaluate_alerts(_make_info(storage_pct=86))
    assert alerts["storage"] == "warn"


def test_evaluate_alerts_storage_critical():
    from modules.health_logger import evaluate_alerts
    alerts = evaluate_alerts(_make_info(storage_pct=96))
    assert alerts["storage"] == "critical"


def test_evaluate_alerts_sd_health_warning():
    from modules.health_logger import evaluate_alerts
    with patch("modules.health_logger.system_helpers.get_sd_health",
               return_value={"life_time_est": "0x05"}):
        alerts = evaluate_alerts(_make_info(sd_life="0x05"))
    assert alerts.get("sd_health") == "warn"


def test_evaluate_alerts_sd_health_critical():
    from modules.health_logger import evaluate_alerts
    with patch("modules.health_logger.system_helpers.get_sd_health",
               return_value={"life_time_est": "0x0B"}):
        alerts = evaluate_alerts(_make_info(sd_life="0x0B"))
    assert alerts.get("sd_health") == "critical"


# ---------------------------------------------------------------------------
# /system_alert_state endpoint tests
# ---------------------------------------------------------------------------

def test_system_alert_state_endpoint(client):
    """GET /system_alert_state returns 200 with the expected JSON shape."""
    res = client.get("/system_alert_state")
    assert res.status_code == 200
    data = res.get_json()
    assert "overall" in data
    assert "alerts" in data


def test_system_alert_state_returns_ok_by_default(client):
    """Default alert state is 'ok' when no snapshots have been taken."""
    res = client.get("/system_alert_state")
    data = res.get_json()
    assert data["overall"] == "ok"
