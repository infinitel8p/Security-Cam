"""Mock sensor for development and testing without GPIO hardware.

Exposes trigger() and release() methods that can be called
programmatically (e.g. via an API endpoint) to simulate a real sensor.
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.mock")


class MockSensor(BaseSensor):
    name = "Mock"
    sensor_type = "mock"
    default_gpio = 0  # not used
    module = "Software only"
    description = "No hardware needed - trigger and release via dashboard or API"
    use_case = "Testing and development without GPIO"
    icon = "wrench"

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return
        self._on_trigger = on_trigger
        self._on_release = on_release
        self._running = True
        log.info("Mock sensor started (use /sensor/mock/trigger and /sensor/mock/release)")

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        log.info("Mock sensor stopped")

    def trigger(self):
        """Simulate a sensor trigger (call from API)."""
        log.info("Mock sensor triggered")
        if self._on_trigger:
            self._on_trigger()

    def release(self):
        """Simulate a sensor release (call from API)."""
        log.info("Mock sensor released")
        if self._on_release:
            self._on_release()
