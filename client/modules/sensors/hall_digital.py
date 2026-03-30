"""KY-003 digital Hall-effect magnetic sensor.

Detects the presence of a magnetic field.  Works like the KY-025
reed switch but uses a Hall-effect IC instead of a mechanical
contact - no moving parts, longer lifespan.

Triggers when a magnet is removed (field lost), releases when a
magnet is brought near (field detected).  Ideal for door/window
open/close detection.

Wiring (3 pins):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO      → GPIO [default pin 13]
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.hall")


class HallDigitalSensor(BaseSensor):
    name = "Hall Magnetic"
    sensor_type = "hall_digital"
    default_gpio = 13
    module = "KY-003"
    description = "Digital Hall-effect sensor - detects magnetic field, no moving parts"
    use_case = "Door / window detection (longer lifespan than reed)"
    icon = "magnet"
    wiring = [
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 13 [pin 33]"},
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
        # KY-003: low when magnet present, high when magnet removed
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.05)
        self._device.when_activated = self._handle_trigger
        self._device.when_deactivated = self._handle_release

        self._running = True
        log.info("Hall digital sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Hall sensor: magnet removed (triggered)")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("Hall sensor: magnet detected (released)")
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
        log.info("Hall digital sensor stopped")
