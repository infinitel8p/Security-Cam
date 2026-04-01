"""Tests for the system_info SSE emitter in health_logger."""

from unittest.mock import patch

import modules.health_logger as hl
import modules.sse as sse_mod


def test_stats_emitter_sends_system_info(client):
    """The SSE stats emitter emits system_info with the correct payload."""
    with patch("modules.system_helpers.get_cpu_temp", return_value=52), \
         patch("modules.system_helpers.get_cpu_load", return_value=23), \
         patch("modules.system_helpers.get_storage_info", return_value={
             "total_gb": 16, "used_gb": 7,
         }), \
         patch("modules.system_helpers.get_ram_usage", return_value={
             "total_mb": 512, "used_mb": 256,
         }), \
         patch("modules.system_helpers.get_uptime", return_value=3600), \
         patch("modules.system_helpers.get_throttle_status", return_value=None), \
         patch("modules.system_helpers.get_sd_health", return_value=None), \
         patch("time.sleep", side_effect=StopIteration):

        sse_mod.emit.reset_mock()

        try:
            hl._stats_emit_loop()
        except StopIteration:
            pass

        sse_mod.emit.assert_called_once_with("system_info", {
            "cpu_temp_celsius": 52,
            "cpu_load_percent": 23,
            "storage_info_gb": {"total_gb": 16, "used_gb": 7},
            "ram_usage_mb": {"total_mb": 512, "used_mb": 256},
            "uptime_seconds": 3600,
            "throttle": None,
            "sd_health": None,
        })


def test_stats_emitter_matches_endpoint_keys(client):
    """SSE payload should have the same top-level keys as /system_info."""
    with patch("modules.system_helpers.get_cpu_temp", return_value=45), \
         patch("modules.system_helpers.get_cpu_load", return_value=10), \
         patch("modules.system_helpers.get_storage_info", return_value={
             "total_gb": 32, "used_gb": 12,
         }), \
         patch("modules.system_helpers.get_ram_usage", return_value={
             "total_mb": 512, "used_mb": 200,
         }), \
         patch("modules.system_helpers.get_uptime", return_value=7200), \
         patch("modules.system_helpers.get_throttle_status", return_value=None), \
         patch("modules.system_helpers.get_sd_health", return_value=None):

        # Get keys from HTTP endpoint
        res = client.get("/system_info")
        endpoint_keys = set(res.get_json().keys())

        # Get keys from SSE emitter
        sse_mod.emit.reset_mock()
        with patch("time.sleep", side_effect=StopIteration):
            try:
                hl._stats_emit_loop()
            except StopIteration:
                pass

        _, sse_data = sse_mod.emit.call_args[0]
        sse_keys = set(sse_data.keys())

        assert sse_keys == endpoint_keys


def test_stats_emitter_survives_error(client):
    """A failing helper should not crash the emitter loop."""
    call_count = 0

    def counting_sleep(_):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise StopIteration

    with patch("modules.system_helpers.get_cpu_temp", side_effect=RuntimeError), \
         patch("time.sleep", side_effect=counting_sleep):

        sse_mod.emit.reset_mock()

        try:
            hl._stats_emit_loop()
        except StopIteration:
            pass

        # Loop survived the error and iterated again
        assert call_count == 2
        # emit was never called because get_cpu_temp raised before it
        sse_mod.emit.assert_not_called()
