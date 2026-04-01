"""Tests for sensor management endpoints."""


def test_sensor_status(client):
    res = client.get("/sensor/status")
    assert res.status_code == 200


def test_sensor_types(client):
    res = client.get("/sensor/types")
    assert res.status_code == 200
    types = res.get_json()
    assert isinstance(types, list)
    assert len(types) > 0
    # Every type should have at least a 'type' and 'name' field
    for t in types:
        assert "type" in t
        assert "name" in t


def test_sensor_configure(client):
    res = client.post("/sensor/configure", json={
        "type": "mock",
        "enabled": False,
        "hold_seconds": 5,
    })
    assert res.status_code == 200


def test_sensor_configure_missing_type(client):
    res = client.post("/sensor/configure", json={"gpio": 22})
    assert res.status_code == 400


def test_sensor_configure_unknown_type(client):
    res = client.post("/sensor/configure", json={"type": "nonexistent"})
    assert res.status_code == 400
    data = res.get_json()
    assert "available" in data


def test_sensor_enable_disable(client):
    res = client.post("/sensor/enable")
    assert res.status_code == 200

    settings = client.get("/settings").get_json()
    assert settings["Sensor"]["enabled"] is True

    res = client.post("/sensor/disable")
    assert res.status_code == 200

    settings = client.get("/settings").get_json()
    assert settings["Sensor"]["enabled"] is False


def test_mock_trigger_no_mock_active(client):
    """Mock trigger/release should fail when no mock sensor is active."""
    res = client.post("/sensor/mock/trigger")
    assert res.status_code == 400

    res = client.post("/sensor/mock/release")
    assert res.status_code == 400
