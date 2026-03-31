"""KY-020 ball tilt switch sensor.

Detects orientation change via a metal ball contact.  Functionally
similar to the KY-017 mercury tilt switch but uses a ball bearing
instead of mercury - more environmentally friendly.

Triggers when tilted beyond threshold, releases when returned to
normal orientation.

Wiring (3 pins):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO (S)  → GPIO [default pin 25]
"""

import logging
import threading

from .base import BaseSensor

log = logging.getLogger("sensor.tilt_ball")


class TiltBallSensor(BaseSensor):
    name = "Tilt Switch (Ball)"
    sensor_type = "tilt_ball"
    default_gpio = 25
    module = "KY-020"
    description = "Ball tilt switch - triggers on orientation change"
    use_case = "Camera tamper detection (alternative to KY-017)"
    icon = "rotate"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO (S)", "connect": "GPIO 25 [pin 22]"},
    )
    calibration_schema = (
        {
            "key": "settle_time",
            "name": "Settle time",
            "type": "range",
            "min": 0,
            "max": 50,
            "default": 5,
            "step": 1,
            "description": "How long the sensor must stay tilted before triggering (in tenths of a second). Filters out brief bumps.",
            "labels": {"min": "Instant", "max": "5s"},
        },
    )

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None
        self._settle_time = kwargs.get("settle_time", 5) / 10.0
        self._settle_timer: threading.Timer | None = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        self._settle_timer = None
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.1)
        self._device.when_deactivated = self._handle_raw_trigger
        self._device.when_activated = self._handle_raw_release

        self._running = True
        log.info("Ball tilt sensor started on GPIO %d (settle_time=%.1fs)",
                 self.gpio, self._settle_time)

    def _handle_raw_trigger(self):
        if self._settle_time <= 0:
            log.info("Tilt detected (ball)")
            if self._on_trigger:
                self._on_trigger()
            return

        log.debug("Tilt detected (ball), waiting %.1fs to settle", self._settle_time)
        self._cancel_settle_timer()
        self._settle_timer = threading.Timer(self._settle_time, self._settled)
        self._settle_timer.daemon = True
        self._settle_timer.start()

    def _settled(self):
        log.info("Tilt sustained for %.1fs - triggering (ball)", self._settle_time)
        self._settle_timer = None
        if self._on_trigger:
            self._on_trigger()

    def _handle_raw_release(self):
        if self._settle_timer is not None:
            log.debug("Tilt released before settle time - ignoring (ball)")
            self._cancel_settle_timer()
            return

        log.info("Ball tilt sensor returned to normal orientation")
        if self._on_release:
            self._on_release()

    def _cancel_settle_timer(self):
        if self._settle_timer is not None:
            self._settle_timer.cancel()
            self._settle_timer = None

    def read_value(self) -> bool | None:
        return self._read_gpio(pull_up=True)

    def stop(self) -> None:
        if not self._running:
            return
        self._cancel_settle_timer()
        if self._device:
            self._device.close()
            self._device = None
        self._running = False
        log.info("Ball tilt sensor stopped")
