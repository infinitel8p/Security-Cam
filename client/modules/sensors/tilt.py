"""KY-017 mercury tilt switch sensor.

Detects orientation change via a mercury ball contact.  Triggers
when the sensor is tilted beyond its threshold angle.  Useful for
tamper detection - mount on the camera and it triggers if someone
moves or repositions it.

Wiring (3 pins):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO (S)  → GPIO [default pin 26]
"""

import logging

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
    wiring = [
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO (S)", "connect": "GPIO 26 [pin 37]"},
    ]

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        # KY-017: state changes when tilted
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.1)
        self._device.when_deactivated = self._handle_trigger
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("Tilt sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Tilt detected (orientation changed)")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("Tilt sensor returned to normal orientation")
        if self._on_release:
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
        log.info("Tilt sensor stopped")
