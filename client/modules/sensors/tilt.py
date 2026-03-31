"""KY-017 mercury tilt switch sensor.

Detects orientation change via a mercury ball contact.  Triggers
when the sensor is tilted beyond its threshold angle.  Useful for
tamper detection - mount on the camera and it triggers if someone
moves or repositions it.

Calibration: settle_time requires the sensor to stay tilted for
a minimum duration before triggering, filtering out brief bumps
and vibrations that cause the mercury to slosh momentarily.

Wiring (3 pins):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO (S)  → GPIO [default pin 26]
"""

import logging
import threading

from .base import BaseSensor

log = logging.getLogger("sensor.tilt")


class TiltSensor(BaseSensor):
    name = "Tilt Switch"
    sensor_type = "tilt"
    default_gpio = 26
    module = "KY-017"
    description = "Mercury tilt switch - triggers on orientation change"
    use_case = "Camera tamper detection (someone moves the camera)"
    icon = "rotate"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO (S)", "connect": "GPIO 26 [pin 37]"},
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
            "description": "How long the sensor must stay tilted before triggering (in tenths of a second). Filters out brief bumps and vibrations.",
            "labels": {"min": "Instant", "max": "5s"},
        },
    )

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None
        # settle_time is stored as tenths of a second for a nice slider (0-50 → 0.0-5.0s)
        self._settle_time = kwargs.get("settle_time", 5) / 10.0
        self._settle_timer: threading.Timer | None = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        self._settle_timer = None
        # KY-017: state changes when tilted
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.1)
        self._device.when_deactivated = self._handle_raw_trigger
        self._device.when_activated = self._handle_raw_release

        self._running = True
        log.info("Tilt sensor started on GPIO %d (settle_time=%.1fs)",
                 self.gpio, self._settle_time)

    def _handle_raw_trigger(self):
        """Raw GPIO trigger - start settle timer or fire immediately."""
        if self._settle_time <= 0:
            log.info("Tilt detected (orientation changed)")
            if self._on_trigger:
                self._on_trigger()
            return

        log.debug("Tilt detected, waiting %.1fs to settle", self._settle_time)
        self._cancel_settle_timer()
        self._settle_timer = threading.Timer(self._settle_time, self._settled)
        self._settle_timer.daemon = True
        self._settle_timer.start()

    def _settled(self):
        """Called after settle_time if sensor is still tilted."""
        log.info("Tilt sustained for %.1fs - triggering", self._settle_time)
        self._settle_timer = None
        if self._on_trigger:
            self._on_trigger()

    def _handle_raw_release(self):
        """Raw GPIO release - cancel settle timer if pending, else fire release."""
        if self._settle_timer is not None:
            log.debug("Tilt released before settle time - ignoring")
            self._cancel_settle_timer()
            return

        log.info("Tilt sensor returned to normal orientation")
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
        log.info("Tilt sensor stopped")
