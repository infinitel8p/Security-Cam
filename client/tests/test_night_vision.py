"""Tests for night vision (IR) detection logic."""

from unittest.mock import patch, MagicMock

import numpy as np
import cv2

import modules.night_vision as nv
import modules.sse as sse_mod


def _make_frame(hue, sat, val, width=100, height=80):
    """Create a BGR frame from uniform HSV values."""
    hsv = np.full((height, width, 3), [hue, sat, val], dtype=np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def test_analyze_frame_magenta():
    """A fully magenta frame should return close to 100%."""
    frame = _make_frame(hue=155, sat=120, val=200)
    pct = nv._analyze_frame(frame)
    assert pct > 90


def test_analyze_frame_green():
    """A green frame should return close to 0%."""
    frame = _make_frame(hue=60, sat=120, val=200)
    pct = nv._analyze_frame(frame)
    assert pct < 1


def test_analyze_frame_low_saturation_ignored():
    """Magenta hue with low saturation should not count."""
    frame = _make_frame(hue=155, sat=20, val=200)
    pct = nv._analyze_frame(frame)
    assert pct < 1


def test_analyze_frame_mixed():
    """A frame that is ~30% magenta should report roughly 30%."""
    h, w = 100, 100
    magenta = np.full((30, w, 3), [155, 120, 200], dtype=np.uint8)
    blue = np.full((70, w, 3), [110, 120, 200], dtype=np.uint8)
    hsv = np.vstack([magenta, blue])
    frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    pct = nv._analyze_frame(frame)
    assert 25 < pct < 35


def test_is_night_mode_default_false():
    """Module should default to night_mode=False."""
    assert nv.is_night_mode() is False


def test_get_state_returns_dict():
    """get_state should return a dict with expected keys."""
    state = nv.get_state()
    assert "active" in state
    assert "magenta_pct" in state


def test_check_loop_emits_on_transition():
    """The check loop should emit an SSE event when night mode activates."""
    magenta_frame = _make_frame(hue=155, sat=120, val=200)

    with patch.object(nv, "_grab_frame", return_value=magenta_frame), \
         patch.object(nv, "_load_settings"), \
         patch("time.sleep", side_effect=StopIteration):

        nv._night_mode = False
        nv._enabled = True
        nv._threshold_pct = 25
        sse_mod.emit.reset_mock()

        try:
            nv._check_loop()
        except StopIteration:
            pass

        sse_mod.emit.assert_called_with("night_mode", {"active": True})


def test_check_loop_no_emit_when_stable():
    """No SSE emission when state doesn't change."""
    magenta_frame = _make_frame(hue=155, sat=120, val=200)
    call_count = 0

    def counting_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise StopIteration

    with patch.object(nv, "_grab_frame", return_value=magenta_frame), \
         patch.object(nv, "_load_settings"), \
         patch("time.sleep", side_effect=counting_sleep):

        # Already in night mode - no transition expected on second iteration
        nv._night_mode = True
        nv._enabled = True
        nv._threshold_pct = 25
        sse_mod.emit.reset_mock()

        try:
            nv._check_loop()
        except StopIteration:
            pass

        sse_mod.emit.assert_not_called()


def test_check_loop_survives_frame_failure():
    """Loop should continue when frame grab fails."""
    call_count = 0

    def counting_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise StopIteration

    with patch.object(nv, "_grab_frame", return_value=None), \
         patch.object(nv, "_load_settings"), \
         patch("time.sleep", side_effect=counting_sleep):

        nv._enabled = True
        sse_mod.emit.reset_mock()

        try:
            nv._check_loop()
        except StopIteration:
            pass

        # Should not have emitted anything since no frame was analyzed
        sse_mod.emit.assert_not_called()


def test_system_info_includes_night_mode(client):
    """The /system_info endpoint should include the night_mode field."""
    with patch("modules.system_helpers.get_cpu_temp", return_value=45), \
         patch("modules.system_helpers.get_cpu_load", return_value=10), \
         patch("modules.system_helpers.get_storage_info", return_value={}), \
         patch("modules.system_helpers.get_ram_usage", return_value={}), \
         patch("modules.system_helpers.get_uptime", return_value=3600), \
         patch("modules.system_helpers.get_throttle_status", return_value=None), \
         patch("modules.system_helpers.get_sd_health", return_value=None):

        res = client.get("/system_info")
        data = res.get_json()
        assert "night_mode" in data
        assert data["night_mode"] is False


def test_disabled_setting_clears_night_mode():
    """When disabled, night mode should be forced off."""
    with patch.object(nv, "_grab_frame") as mock_grab, \
         patch.object(nv, "_load_settings"), \
         patch("time.sleep", side_effect=StopIteration):

        nv._night_mode = True
        nv._enabled = False
        sse_mod.emit.reset_mock()

        try:
            nv._check_loop()
        except StopIteration:
            pass

        # Should have emitted off transition
        sse_mod.emit.assert_called_with("night_mode", {"active": False})
        assert nv._night_mode is False
        # Frame grab should not be called when disabled
        mock_grab.assert_not_called()
