"""Read API, MediaMTX, and install log files for the dashboard log viewer."""

import glob
import os
import re

LOG_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "logs")

# Matches the structured log format: "2026-04-01 09:54:29 [INFO] presence: message"
_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"\[(?P<level>\w+)]\s+"
    r"(?P<source>\S+?):\s+"
    r"(?P<message>.*)$"
)


def _parse_line(line: str) -> dict | None:
    m = _LINE_RE.match(line)
    if not m:
        return None
    return {
        "ts": m.group("ts"),
        "level": m.group("level"),
        "source": m.group("source"),
        "message": m.group("message"),
    }


def get_api_logs(limit: int = 500, level: str | None = None,
                 search: str | None = None) -> list[dict]:
    """Return parsed API log lines (newest first).

    Reads the current log file and rotated backups (.1, .2, .3) until
    *limit* matching lines are collected.
    """
    log_dir = os.path.join(LOG_ROOT, "api")
    base = os.path.join(log_dir, "security-cam.log")

    # Rotated files: .1 is most recent, .2 next, etc.
    files = [base] + sorted(glob.glob(base + ".*"),
                            key=lambda f: int(f.rsplit(".", 1)[-1]) if f.rsplit(".", 1)[-1].isdigit() else 999)

    level_upper = level.upper() if level else None
    search_lower = search.lower() if search else None
    results: list[dict] = []

    for path in files:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            continue

        for raw in reversed(lines):
            raw = raw.rstrip("\n")
            if not raw:
                continue
            parsed = _parse_line(raw)
            if parsed is None:
                # Continuation line — attach to previous entry if any
                if results:
                    results[-1]["message"] += "\n" + raw
                continue
            if level_upper and parsed["level"] != level_upper:
                continue
            if search_lower and search_lower not in raw.lower():
                continue
            results.append(parsed)
            if len(results) >= limit:
                return results

    return results


# MediaMTX log format: "2026/04/01 10:00:00 INF [RTSP] listener opened on :8554"
_MTX_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>\w+)\s+"
    r"(?:\[(?P<source>[^\]]+)]\s+)?"
    r"(?P<message>.*)$"
)

_MTX_LEVEL_MAP = {
    "DBG": "DEBUG",
    "INF": "INFO",
    "WAR": "WARNING",
    "ERR": "ERROR",
}


def _parse_mtx_line(line: str) -> dict | None:
    m = _MTX_LINE_RE.match(line)
    if not m:
        return None
    raw_level = m.group("level")
    return {
        "ts": m.group("ts").replace("/", "-"),
        "level": _MTX_LEVEL_MAP.get(raw_level, raw_level),
        "source": m.group("source") or "mediamtx",
        "message": m.group("message"),
    }


def get_mediamtx_logs(limit: int = 500, level: str | None = None,
                      search: str | None = None) -> list[dict]:
    """Return parsed MediaMTX log lines (newest first)."""
    log_file = os.path.join(LOG_ROOT, "mediamtx", "mediamtx.log")
    if not os.path.isfile(log_file):
        return []

    level_upper = level.upper() if level else None
    search_lower = search.lower() if search else None
    results: list[dict] = []

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []

    for raw in reversed(lines):
        raw = raw.rstrip("\n")
        if not raw:
            continue
        parsed = _parse_mtx_line(raw)
        if parsed is None:
            if results:
                results[-1]["message"] += "\n" + raw
            continue
        if level_upper and parsed["level"] != level_upper:
            continue
        if search_lower and search_lower not in raw.lower():
            continue
        results.append(parsed)
        if len(results) >= limit:
            return results

    return results


# Directories that contain script/setup log files (plain text).
# api/ and mediamtx/ are handled by dedicated parsers above.
_SCRIPT_LOG_DIRS = ["install", "update", "ap-setup"]


def get_install_logs() -> list[dict]:
    """Return a list of script/setup log files from all log subdirectories (newest first).

    Scans install/, update/, ap-setup/, and any other subdirectory under
    logs/ that isn't already handled by a dedicated parser (api/, mediamtx/).
    """
    excluded = {"api", "mediamtx"}
    entries = []

    if not os.path.isdir(LOG_ROOT):
        return []

    # Scan known dirs + any new subdirectories that appear in the future
    subdirs = set()
    try:
        for name in os.listdir(LOG_ROOT):
            full = os.path.join(LOG_ROOT, name)
            if os.path.isdir(full) and name not in excluded:
                subdirs.add(name)
    except OSError:
        return []

    for subdir in subdirs:
        dir_path = os.path.join(LOG_ROOT, subdir)
        try:
            names = os.listdir(dir_path)
        except OSError:
            continue
        for name in names:
            if not name.endswith(".log"):
                continue
            path = os.path.join(dir_path, name)
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            # Use "subdir/filename" as the key so files from different
            # directories don't collide and the source is clear.
            entries.append({
                "name": f"{subdir}/{name}",
                "size": size,
                "category": subdir,
            })

    # Sort newest first by filename (timestamps are embedded in names)
    entries.sort(key=lambda e: e["name"], reverse=True)
    return entries


def get_install_log_content(filepath: str) -> str | None:
    """Return the content of a specific script log file.

    Accepts paths like "install/2026-04-01_09-51-07.log" or
    "update/2026-04-01_10-00-00.log". Returns None if the file
    doesn't exist or the path is invalid.
    """
    # Allow exactly one slash: "subdir/filename.log"
    if ".." in filepath or "\\" in filepath:
        return None
    parts = filepath.split("/")
    if len(parts) != 2:
        return None
    subdir, filename = parts
    # Block access to api/ and mediamtx/ runtime logs via this endpoint
    if subdir in ("api", "mediamtx"):
        return None

    path = os.path.join(LOG_ROOT, subdir, filename)
    if not os.path.isfile(path):
        return None

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None
