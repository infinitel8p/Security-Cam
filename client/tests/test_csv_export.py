"""Tests for the CSV event export endpoint."""

import csv
import io
from unittest.mock import patch


def _mock_events():
    return [
        {"ts": "2026-04-01T10:00:00+00:00", "type": "system_boot", "severity": "ok"},
        {"ts": "2026-04-01T10:05:00+00:00", "type": "sensor_triggered", "severity": "warn", "detail": "PIR motion"},
        {"ts": "2026-04-01T10:05:01+00:00", "type": "recording_started", "severity": "warn"},
        {"ts": "2026-04-01T10:06:00+00:00", "type": "recording_stopped", "severity": "ok"},
    ]


def test_csv_export_returns_csv(client):
    with patch("modules.event_logger.get_events", return_value=_mock_events()):
        res = client.get("/event_history/csv")

    assert res.status_code == 200
    assert res.content_type.startswith("text/csv")
    assert "attachment" in res.headers.get("Content-Disposition", "")


def test_csv_export_has_header_row(client):
    with patch("modules.event_logger.get_events", return_value=_mock_events()):
        res = client.get("/event_history/csv")

    reader = csv.reader(io.StringIO(res.get_data(as_text=True)))
    header = next(reader)
    assert header == ["timestamp", "type", "severity", "detail"]


def test_csv_export_row_count(client):
    events = _mock_events()
    with patch("modules.event_logger.get_events", return_value=events):
        res = client.get("/event_history/csv")

    reader = csv.reader(io.StringIO(res.get_data(as_text=True)))
    rows = list(reader)
    # header + data rows
    assert len(rows) == len(events) + 1


def test_csv_export_detail_column(client):
    with patch("modules.event_logger.get_events", return_value=_mock_events()):
        res = client.get("/event_history/csv")

    reader = csv.reader(io.StringIO(res.get_data(as_text=True)))
    next(reader)  # skip header
    rows = list(reader)

    # Second event has detail "PIR motion"
    assert rows[1][3] == "PIR motion"
    # First event has no detail - should be empty string
    assert rows[0][3] == ""


def test_csv_export_empty(client):
    with patch("modules.event_logger.get_events", return_value=[]):
        res = client.get("/event_history/csv")

    assert res.status_code == 200
    reader = csv.reader(io.StringIO(res.get_data(as_text=True)))
    rows = list(reader)
    assert len(rows) == 1  # header only


def test_csv_export_respects_hours_param(client):
    with patch("modules.event_logger.get_events", return_value=[]) as mock:
        client.get("/event_history/csv?hours=72")
        mock.assert_called_once_with(72)


def test_csv_export_clamps_hours(client):
    with patch("modules.event_logger.get_events", return_value=[]) as mock:
        client.get("/event_history/csv?hours=99999")
        mock.assert_called_once_with(4380)
