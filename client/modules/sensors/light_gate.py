"""KY-010 photo interrupter (light gate) sensor.

Small slotted optical sensor (~5mm gap) with an IR emitter and
receiver.  Triggers when the beam is blocked by an object in the
slot.  Useful as an alarm trigger when a pin or bolt is pulled
from the slot.  Requires some mechanical effort to mount properly.

Wiring (3 pins):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO      → GPIO [default pin 6]
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.light_gate")


class LightGateSensor(BaseSensor):
    name = "Light Gate"
    sensor_type = "light_gate"
    default_gpio = 6
    module = "KY-010"
    description = "Photo interrupter - triggers when IR beam in ~5mm slot is blocked"
    use_case = "Alarm when pin/bolt is removed, rotation counting"
    icon = "gate"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 6 [pin 31]"},
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
        # KY-010: high when beam clear, low when beam blocked
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.05)
        self._device.when_deactivated = self._handle_trigger
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("Light gate sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Light gate beam blocked")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("Light gate beam restored")
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
        log.info("Light gate sensor stopped")
