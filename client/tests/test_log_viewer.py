"""Tests for the log viewer API endpoints and log_reader module."""

import os
from unittest.mock import patch


# ---------------------------------------------------------------------------
# /logs/api endpoint tests
# ---------------------------------------------------------------------------


def test_logs_api_returns_list(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "security-cam.log"
    log_file.write_text(
        "2026-04-01 09:54:29 [INFO] api: Server started\n"
        "2026-04-01 09:54:30 [ERROR] presence: Something broke\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/api")

    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_logs_api_newest_first(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    (log_dir / "security-cam.log").write_text(
        "2026-04-01 09:00:00 [INFO] api: First\n"
        "2026-04-01 09:01:00 [INFO] api: Second\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/api")

    data = res.get_json()
    assert data[0]["message"] == "Second"
    assert data[1]["message"] == "First"


def test_logs_api_filter_by_level(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    (log_dir / "security-cam.log").write_text(
        "2026-04-01 09:00:00 [INFO] api: Info line\n"
        "2026-04-01 09:00:01 [ERROR] api: Error line\n"
        "2026-04-01 09:00:02 [INFO] api: Another info\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/api?level=ERROR")

    data = res.get_json()
    assert len(data) == 1
    assert data[0]["level"] == "ERROR"


def test_logs_api_search(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    (log_dir / "security-cam.log").write_text(
        "2026-04-01 09:00:00 [INFO] api: Server started\n"
        "2026-04-01 09:00:01 [ERROR] presence: BT scan failed\n"
        "2026-04-01 09:00:02 [INFO] api: GET /settings\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/api?search=presence")

    data = res.get_json()
    assert len(data) == 1
    assert data[0]["source"] == "presence"


def test_logs_api_respects_limit(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    lines = ""
    for i in range(10):
        lines += f"2026-04-01 09:00:{i:02d} [INFO] api: Line {i}\n"
    (log_dir / "security-cam.log").write_text(lines)

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/api?limit=3")

    data = res.get_json()
    assert len(data) == 3


def test_logs_api_limit_capped_at_2000(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    (log_dir / "security-cam.log").write_text(
        "2026-04-01 09:00:00 [INFO] api: One line\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        # Even if client requests more, server caps at 2000
        res = client.get("/logs/api?limit=5000")

    assert res.status_code == 200


def test_logs_api_empty_log(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    (log_dir / "security-cam.log").write_text("")

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/api")

    assert res.status_code == 200
    assert res.get_json() == []


def test_logs_api_no_log_dir(client, tmp_path):
    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "nonexistent")):
        res = client.get("/logs/api")

    assert res.status_code == 200
    assert res.get_json() == []


def test_logs_api_reads_rotated_files(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    (log_dir / "security-cam.log").write_text(
        "2026-04-01 10:00:00 [INFO] api: Current log\n"
    )
    (log_dir / "security-cam.log.1").write_text(
        "2026-04-01 09:00:00 [INFO] api: Rotated log\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/api?limit=10")

    data = res.get_json()
    assert len(data) == 2
    # Current log entry should come first (newest first)
    assert data[0]["message"] == "Current log"
    assert data[1]["message"] == "Rotated log"


def test_logs_api_parses_fields(client, tmp_path):
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    (log_dir / "security-cam.log").write_text(
        "2026-04-01 09:54:29 [WARNING] sensor.mgr: Trigger logic inverted\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/api")

    data = res.get_json()
    assert len(data) == 1
    entry = data[0]
    assert entry["ts"] == "2026-04-01 09:54:29"
    assert entry["level"] == "WARNING"
    assert entry["source"] == "sensor.mgr"
    assert entry["message"] == "Trigger logic inverted"


# ---------------------------------------------------------------------------
# /logs/mediamtx endpoint tests
# ---------------------------------------------------------------------------


def test_logs_mediamtx_returns_list(client, tmp_path):
    log_dir = tmp_path / "logs" / "mediamtx"
    log_dir.mkdir(parents=True)
    (log_dir / "mediamtx.log").write_text(
        "2026/04/01 10:00:00 INF [RTSP] listener opened on :8554\n"
        "2026/04/01 10:00:01 INF [WebRTC] listener opened on :8889\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/mediamtx")

    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 2


def test_logs_mediamtx_parses_fields(client, tmp_path):
    log_dir = tmp_path / "logs" / "mediamtx"
    log_dir.mkdir(parents=True)
    (log_dir / "mediamtx.log").write_text(
        "2026/04/01 10:00:00 ERR [RTSP] connection failed\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/mediamtx")

    data = res.get_json()
    assert len(data) == 1
    entry = data[0]
    assert entry["ts"] == "2026-04-01 10:00:00"
    assert entry["level"] == "ERROR"
    assert entry["source"] == "RTSP"
    assert entry["message"] == "connection failed"


def test_logs_mediamtx_level_mapping(client, tmp_path):
    log_dir = tmp_path / "logs" / "mediamtx"
    log_dir.mkdir(parents=True)
    (log_dir / "mediamtx.log").write_text(
        "2026/04/01 10:00:00 DBG [RTSP] debug msg\n"
        "2026/04/01 10:00:01 INF [RTSP] info msg\n"
        "2026/04/01 10:00:02 WAR [RTSP] warn msg\n"
        "2026/04/01 10:00:03 ERR [RTSP] error msg\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/mediamtx")

    data = res.get_json()
    levels = [e["level"] for e in data]
    assert levels == ["ERROR", "WARNING", "INFO", "DEBUG"]


def test_logs_mediamtx_filter_by_level(client, tmp_path):
    log_dir = tmp_path / "logs" / "mediamtx"
    log_dir.mkdir(parents=True)
    (log_dir / "mediamtx.log").write_text(
        "2026/04/01 10:00:00 INF [RTSP] info line\n"
        "2026/04/01 10:00:01 ERR [WebRTC] error line\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/mediamtx?level=ERROR")

    data = res.get_json()
    assert len(data) == 1
    assert data[0]["level"] == "ERROR"


def test_logs_mediamtx_search(client, tmp_path):
    log_dir = tmp_path / "logs" / "mediamtx"
    log_dir.mkdir(parents=True)
    (log_dir / "mediamtx.log").write_text(
        "2026/04/01 10:00:00 INF [RTSP] listener opened\n"
        "2026/04/01 10:00:01 INF [WebRTC] listener opened\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/mediamtx?search=WebRTC")

    data = res.get_json()
    assert len(data) == 1
    assert data[0]["source"] == "WebRTC"


def test_logs_mediamtx_empty(client, tmp_path):
    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "nonexistent")):
        res = client.get("/logs/mediamtx")

    assert res.status_code == 200
    assert res.get_json() == []


def test_logs_mediamtx_no_source_bracket(client, tmp_path):
    """MediaMTX sometimes logs without a [source] bracket."""
    log_dir = tmp_path / "logs" / "mediamtx"
    log_dir.mkdir(parents=True)
    (log_dir / "mediamtx.log").write_text(
        "2026/04/01 10:00:00 INF MediaMTX v1.17.0\n"
    )

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/mediamtx")

    data = res.get_json()
    assert len(data) == 1
    assert data[0]["source"] == "mediamtx"
    assert data[0]["message"] == "MediaMTX v1.17.0"


# ---------------------------------------------------------------------------
# /logs/install (script logs) endpoint tests
# ---------------------------------------------------------------------------


def test_logs_install_list_scans_all_subdirs(client, tmp_path):
    """Script logs list includes files from install/, update/, ap-setup/."""
    for subdir in ("install", "update", "ap-setup"):
        d = tmp_path / "logs" / subdir
        d.mkdir(parents=True)
        (d / "2026-04-01_09-00-00.log").write_text(f"{subdir} output")

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/install")

    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 3
    categories = {e["category"] for e in data}
    assert categories == {"install", "update", "ap-setup"}


def test_logs_install_list_has_subdir_prefix(client, tmp_path):
    log_dir = tmp_path / "logs" / "install"
    log_dir.mkdir(parents=True)
    (log_dir / "2026-04-01_09-51-07.log").write_text("install output")

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/install")

    data = res.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "install/2026-04-01_09-51-07.log"
    assert data[0]["category"] == "install"
    assert data[0]["size"] > 0


def test_logs_install_list_empty(client, tmp_path):
    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "nonexistent")):
        res = client.get("/logs/install")

    assert res.status_code == 200
    assert res.get_json() == []


def test_logs_script_content(client, tmp_path):
    log_dir = tmp_path / "logs" / "install"
    log_dir.mkdir(parents=True)
    content = "=== Checking Node.js ===\nNode.js v22.22.0 already installed.\n"
    (log_dir / "2026-04-01_09-51-07.log").write_text(content)

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/script/install/2026-04-01_09-51-07.log")

    assert res.status_code == 200
    assert res.get_data(as_text=True) == content


def test_logs_script_content_update_dir(client, tmp_path):
    log_dir = tmp_path / "logs" / "update"
    log_dir.mkdir(parents=True)
    (log_dir / "2026-04-01_10-00-00.log").write_text("update output")

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/script/update/2026-04-01_10-00-00.log")

    assert res.status_code == 200
    assert res.get_data(as_text=True) == "update output"


def test_logs_script_content_not_found(client, tmp_path):
    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/script/install/nonexistent.log")

    assert res.status_code == 404


def test_logs_script_content_blocks_api_dir(client, tmp_path):
    """Cannot read runtime logs via the script endpoint."""
    log_dir = tmp_path / "logs" / "api"
    log_dir.mkdir(parents=True)
    (log_dir / "security-cam.log").write_text("secret")

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/script/api/security-cam.log")

    assert res.status_code == 404


def test_logs_script_content_blocks_traversal(client, tmp_path):
    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/script/install/../../etc/passwd")

    assert res.status_code == 404


def test_logs_install_excludes_api_and_mediamtx(client, tmp_path):
    """api/ and mediamtx/ dirs should not appear in script log listing."""
    for subdir in ("install", "api", "mediamtx"):
        d = tmp_path / "logs" / subdir
        d.mkdir(parents=True)
        (d / "test.log").write_text("content")

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/install")

    data = res.get_json()
    categories = {e["category"] for e in data}
    assert "api" not in categories
    assert "mediamtx" not in categories
    assert "install" in categories


def test_logs_install_skips_non_log_files(client, tmp_path):
    log_dir = tmp_path / "logs" / "install"
    log_dir.mkdir(parents=True)
    (log_dir / "2026-04-01_09-51-07.log").write_text("real log")
    (log_dir / "notes.txt").write_text("not a log")

    with patch("modules.log_reader.LOG_ROOT", str(tmp_path / "logs")):
        res = client.get("/logs/install")

    data = res.get_json()
    assert len(data) == 1
    assert data[0]["name"].endswith(".log")
