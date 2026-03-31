"""KY-032 IR obstacle avoidance / proximity sensor.

Emits an infrared beam and detects its reflection.  The digital
output triggers when an object is within the detection range
(adjustable via the onboard potentiometer, roughly 2-40 cm).

Useful for detecting someone approaching a door, window, or the
camera itself at close range.

Wiring (3 pins - active-low):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  OUT     → GPIO [default pin 24]

Note: Adjust the onboard potentiometer to set detection distance.
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.ir_prox")


class IRProximitySensor(BaseSensor):
    name = "IR Proximity"
    sensor_type = "ir_proximity"
    default_gpio = 24
    module = "KY-032"
    description = "IR obstacle sensor - triggers when something is within range"
    use_case = "Detect someone approaching a door, window, or camera"
    icon = "eye"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "OUT", "connect": "GPIO 24 [pin 18]"},
    )
    wiring_note = "Adjust the onboard potentiometer to set detection distance (~2-40 cm). The sensor outputs LOW when an object is detected."

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        # KY-032: active-low - output goes LOW when object detected
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.05)
        self._device.when_deactivated = self._handle_trigger
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("IR proximity sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("IR proximity: object detected")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("IR proximity: object cleared")
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
        log.info("IR proximity sensor stopped")
