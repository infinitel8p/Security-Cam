"""KY-036 metal touch sensor.

Capacitive touch sensor that triggers when a person touches the
metal contact pad.  Useful for detecting if someone touches the
camera housing or a conductive surface near it.

Wiring (3 pins - ignore AO if present):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO      → GPIO [default pin 16]
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.touch")


class TouchSensor(BaseSensor):
    name = "Touch Sensor"
    sensor_type = "touch"
    default_gpio = 16
    module = "KY-036"
    description = "Capacitive metal touch sensor - triggers on skin contact"
    use_case = "Detect touching of camera housing or door handle"
    icon = "hand"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 16 [pin 36]"},
    )

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        # KY-036: low normally, goes high on touch
        self._device = DigitalInputDevice(self.gpio, pull_up=False,
                                          bounce_time=0.05)
        self._device.when_activated = self._handle_trigger
        self._device.when_deactivated = self._handle_release

        self._running = True
        log.info("Touch sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Touch detected")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("Touch released")
        if self._on_release:
            self._on_release()

    def read_value(self) -> bool | None:
        return self._read_gpio(pull_up=False)

    def stop(self) -> None:
        if not self._running:
            return
        if self._device:
            self._device.close()
            self._device = None
        self._running = False
        log.info("Touch sensor stopped")
