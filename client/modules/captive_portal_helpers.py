"""Toggle the captive-portal iptables rule that redirects port 80 → 3000.

When enabled, devices connecting to the AP are shown the dashboard via the
OS captive-portal popup (macOS, Android, Windows, etc.).  When disabled, the
iptables rule is removed so the popup never appears.
"""

import logging
import subprocess

log = logging.getLogger("captive_portal")

AP_INTERFACE = "ap0"
_RULE_ARGS = [
    "-i", AP_INTERFACE, "-p", "tcp",
    "--dport", "80", "-j", "REDIRECT", "--to-port", "3000",
]


def rule_exists() -> bool:
    """Check whether the PREROUTING redirect rule is active."""
    result = subprocess.run(
        ["sudo", "iptables", "-t", "nat", "-C", "PREROUTING"] + _RULE_ARGS,
        capture_output=True,
    )
    return result.returncode == 0


def enable() -> bool:
    """Add the iptables rule (idempotent). Returns True on success."""
    if rule_exists():
        log.debug("Captive portal rule already active")
        return True
    try:
        subprocess.run(
            ["sudo", "iptables", "-t", "nat", "-A", "PREROUTING"] + _RULE_ARGS,
            capture_output=True, check=True,
        )
        log.info("Captive portal rule added")
        return True
    except subprocess.CalledProcessError as e:
        log.error("Failed to add captive portal rule: %s", e)
        return False


def disable() -> bool:
    """Remove the iptables rule (idempotent). Returns True on success."""
    if not rule_exists():
        log.debug("Captive portal rule already absent")
        return True
    try:
        subprocess.run(
            ["sudo", "iptables", "-t", "nat", "-D", "PREROUTING"] + _RULE_ARGS,
            capture_output=True, check=True,
        )
        log.info("Captive portal rule removed")
        return True
    except subprocess.CalledProcessError as e:
        log.error("Failed to remove captive portal rule: %s", e)
        return False


def sync(enabled: bool) -> None:
    """Ensure iptables matches the persisted setting (called on startup)."""
    if enabled:
        enable()
    else:
        disable()
