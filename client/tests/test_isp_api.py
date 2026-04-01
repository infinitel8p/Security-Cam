"""Tests for the /isp_settings ISP image-quality endpoint."""


def test_isp_settings_get(client):
    """GET /isp_settings returns current ISP values."""
    res = client.get("/isp_settings")
    assert res.status_code == 200
    data = res.get_json()
    assert data["brightness"] == 0
    assert data["contrast"] == 1
    assert data["saturation"] == 1
    assert data["sharpness"] == 1
    assert data["ev"] == 0
    assert data["awb"] == "auto"
    assert data["exposure"] == "normal"
    assert data["denoise"] == "off"
    assert data["metering"] == "centre"


def test_isp_settings_post_single(client):
    """POST /isp_settings with a single param succeeds."""
    res = client.post("/isp_settings", json={"brightness": 0.5})
    assert res.status_code == 200


def test_isp_settings_post_multiple(client):
    """POST /isp_settings with multiple params succeeds."""
    res = client.post("/isp_settings", json={
        "brightness": -0.3,
        "contrast": 2,
        "saturation": 1.5,
        "sharpness": 3,
        "ev": 2,
        "awb": "daylight",
        "exposure": "short",
        "denoise": "cdn_fast",
        "metering": "spot",
    })
    assert res.status_code == 200


def test_isp_settings_post_empty(client):
    """POST /isp_settings with empty body returns 400."""
    res = client.post("/isp_settings", json={})
    assert res.status_code == 400


def test_isp_settings_post_invalid_awb(client):
    """POST /isp_settings with invalid AWB value returns 400."""
    res = client.post("/isp_settings", json={"awb": "nonsense"})
    assert res.status_code == 400


def test_isp_settings_post_invalid_exposure(client):
    """POST /isp_settings with invalid exposure value returns 400."""
    res = client.post("/isp_settings", json={"exposure": "ultra"})
    assert res.status_code == 400


def test_isp_settings_post_invalid_denoise(client):
    """POST /isp_settings with invalid denoise value returns 400."""
    res = client.post("/isp_settings", json={"denoise": "max"})
    assert res.status_code == 400


def test_isp_settings_post_invalid_metering(client):
    """POST /isp_settings with invalid metering value returns 400."""
    res = client.post("/isp_settings", json={"metering": "average"})
    assert res.status_code == 400


def test_isp_settings_persisted(client):
    """POST /isp_settings persists values in settings.json."""
    client.post("/isp_settings", json={"brightness": 0.8, "awb": "cloudy"})
    res = client.get("/settings")
    assert res.status_code == 200
    isp = res.get_json().get("ISP", {})
    assert isp.get("brightness") == 0.8
    assert isp.get("awb") == "cloudy"


def test_isp_settings_brightness_out_of_range(client):
    """POST /isp_settings with brightness > 1 returns 400."""
    res = client.post("/isp_settings", json={"brightness": 5})
    assert res.status_code == 400


def test_isp_settings_brightness_below_range(client):
    """POST /isp_settings with brightness < -1 returns 400."""
    res = client.post("/isp_settings", json={"brightness": -2})
    assert res.status_code == 400


def test_isp_settings_contrast_out_of_range(client):
    """POST /isp_settings with contrast > 16 returns 400."""
    res = client.post("/isp_settings", json={"contrast": 20})
    assert res.status_code == 400


def test_isp_settings_ev_out_of_range(client):
    """POST /isp_settings with EV > 10 returns 400."""
    res = client.post("/isp_settings", json={"ev": 15})
    assert res.status_code == 400


def test_isp_settings_ignores_unknown_keys(client):
    """POST /isp_settings ignores keys not in ISP_KEYS."""
    res = client.post("/isp_settings", json={
        "brightness": 0.1,
        "unknown_param": 42,
    })
    assert res.status_code == 200
