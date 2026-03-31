"""KY-031 knock/tap sensor.

Detects taps, knocks, or light impacts via a spring-contact switch.
Similar to KY-002 vibration but tuned for deliberate taps rather
than sustained vibration.  Produces brief pulses - the sensor
manager's hold timeout keeps recording running through repeated knocks.

Calibration: pulse_count and pulse_window let you require multiple
knocks within a time window before triggering.

Wiring (3 pins):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO (S)  → GPIO [default pin 19]
"""

import logging
import threading
import time

from .base import BaseSensor

log = logging.getLogger("sensor.knock")


class KnockSensor(BaseSensor):
    name = "Knock / Tap"
    sensor_type = "knock"
    default_gpio = 19
    module = "KY-031"
    description = "Knock sensor - detects taps and deliberate knocks"
    use_case = "Detect knocking on door or tapping on window"
    icon = "zap"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO (S)", "connect": "GPIO 19 [pin 35]"},
    )
    calibration_schema = (
        {
            "key": "pulse_count",
            "name": "Knock threshold",
            "type": "range",
            "min": 1,
            "max": 10,
            "default": 3,
            "step": 1,
            "description": "Number of knocks required to trigger. Set to 3 to detect a typical 'knock-knock-knock'.",
            "labels": {"min": "Single tap", "max": "Many knocks"},
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
            "description": "Time window to count knocks in. Only used when knock threshold > 1.",
            "labels": {"min": "1s", "max": "30s"},
        },
    )

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None
        self._pulse_count = kwargs.get("pulse_count", 3)
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
        # KY-031: normally high, pulses low on knock
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.1)
        self._device.when_deactivated = self._handle_pulse
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("Knock sensor started on GPIO %d (pulse_count=%d, window=%ds)",
                 self.gpio, self._pulse_count, self._pulse_window)

    def _handle_pulse(self):
        """Count knocks and only trigger when threshold is met."""
        if self._pulse_count <= 1:
            log.info("Knock detected")
            if self._on_trigger:
                self._on_trigger()
            return

        now = time.monotonic()
        with self._pulse_lock:
            cutoff = now - self._pulse_window
            self._pulse_times = [t for t in self._pulse_times if t > cutoff]
            self._pulse_times.append(now)
            count = len(self._pulse_times)

        log.debug("Knock pulse %d/%d", count, self._pulse_count)
        if count >= self._pulse_count:
            log.info("Knock threshold reached (%d knocks in %ds)",
                     self._pulse_count, self._pulse_window)
            with self._pulse_lock:
                self._pulse_times.clear()
            if self._on_trigger:
                self._on_trigger()

    def _handle_release(self):
        log.debug("Knock pulse ended")
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
        log.info("Knock sensor stopped")
