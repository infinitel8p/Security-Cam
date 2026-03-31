"""KY-002 vibration/shock sensor.

Detects impact or vibration via a spring-contact switch on GPIO.
Produces brief digital pulses on each vibration - there is no
sustained "triggered" state, so on_release is called immediately
after on_trigger.  The sensor manager's hold timeout keeps the
recording running through repeated vibrations.

Calibration: pulse_count and pulse_window let you require multiple
impacts within a time window before triggering, filtering out
single accidental bumps.

Wiring (3 pins - ignore AO if present):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO      → GPIO [default pin 5]
"""

import logging
import threading
import time

from .base import BaseSensor

log = logging.getLogger("sensor.vibration")


class VibrationSensor(BaseSensor):
    name = "Vibration / Shock"
    sensor_type = "vibration"
    default_gpio = 5
    module = "KY-002"
    description = "Spring-contact shock sensor - brief pulse on impact"
    use_case = "Door slam, forced entry, impact detection"
    icon = "zap"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 5 [pin 29]"},
    )
    calibration_schema = (
        {
            "key": "pulse_count",
            "name": "Pulse threshold",
            "type": "range",
            "min": 1,
            "max": 20,
            "default": 1,
            "step": 1,
            "description": "Number of vibrations required to trigger. Higher values filter out accidental bumps.",
            "labels": {"min": "Sensitive", "max": "Firm"},
        },
        {
            "key": "pulse_window",
            "name": "Counting window",
            "type": "range",
            "min": 1,
            "max": 30,
            "default": 5,
            "step": 1,
            "unit": "seconds",
            "description": "Time window to count pulses in. Only used when pulse threshold > 1.",
            "labels": {"min": "1s", "max": "30s"},
        },
    )

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None
        self._pulse_count = kwargs.get("pulse_count", 1)
        self._pulse_window = kwargs.get("pulse_window", 5)
        self._pulse_times: list[float] = []
        self._pulse_lock = threading.Lock()

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        self._pulse_times = []
        # KY-002: normally high, pulses low on vibration
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.1)
        self._device.when_deactivated = self._handle_pulse
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("Vibration sensor started on GPIO %d (pulse_count=%d, window=%ds)",
                 self.gpio, self._pulse_count, self._pulse_window)

    def _handle_pulse(self):
        """Count pulses and only trigger when threshold is met."""
        if self._pulse_count <= 1:
            log.info("Vibration detected")
            if self._on_trigger:
                self._on_trigger()
            return

        now = time.monotonic()
        with self._pulse_lock:
            # Discard pulses outside the window
            cutoff = now - self._pulse_window
            self._pulse_times = [t for t in self._pulse_times if t > cutoff]
            self._pulse_times.append(now)
            count = len(self._pulse_times)

        log.debug("Vibration pulse %d/%d", count, self._pulse_count)
        if count >= self._pulse_count:
            log.info("Vibration threshold reached (%d pulses in %ds)",
                     self._pulse_count, self._pulse_window)
            with self._pulse_lock:
                self._pulse_times.clear()
            if self._on_trigger:
                self._on_trigger()

    def _handle_release(self):
        log.debug("Vibration pulse ended")
        if self._pulse_count <= 1 and self._on_release:
            self._on_release()

    def read_value(self) -> bool | None:
        return self._read_gpio(pull_up=True)

    def stop(self) -> None:
        if not self._running:
            return
        if self._device:
            self._device.close()
            self._device = None
        self._running = False
        log.info("Vibration sensor stopped")
