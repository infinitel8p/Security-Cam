"""KY-021 mini magnetic reed switch sensor.

Compact reed switch - functionally identical to the KY-025 but in
a smaller form factor.  Triggers when the magnet is removed (door
opens), releases when the magnet returns (door closes).

Wiring (2 pins - active-low, no VCC needed):
  GND → GND  [pin 14]
  S   → GPIO [default pin 20]

Note: The KY-021 has only 2 pins (signal + ground) unlike the
KY-025 which has 3 (VCC + GND + DO).  The internal pull-up
resistor on the GPIO pin provides the logic-high reference.
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.mini_reed")


class MiniReedSensor(BaseSensor):
    name = "Mini Reed Switch"
    sensor_type = "mini_reed"
    default_gpio = 20
    module = "KY-021"
    description = "Compact reed switch - same function as KY-025, smaller form factor"
    use_case = "Door / window open detection (tight spaces)"
    icon = "magnet"
    wiring = (
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "S (Signal)", "connect": "GPIO 20 [pin 38]"},
    )
    wiring_note = "Only 2 pins - the internal GPIO pull-up provides the logic reference. No VCC needed."

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        # KY-021: closed (low) when magnet near, open (high) when magnet removed
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.05)
        self._device.when_activated = self._handle_trigger
        self._device.when_deactivated = self._handle_release

        self._running = True
        log.info("Mini reed switch started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Mini reed: magnet removed (door opened)")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("Mini reed: magnet detected (door closed)")
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
        log.info("Mini reed switch stopped")
