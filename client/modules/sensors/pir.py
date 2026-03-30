"""PIR (passive infrared) motion sensor.

Triggers when motion is detected.  PIR sensors typically hold their
output high for a hardware-defined period, so on_release fires when
the sensor's output goes low again.  The sensor manager's hold timeout
provides an additional buffer.
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.pir")


class PIRSensor(BaseSensor):
    name = "PIR Motion"
    sensor_type = "pir"
    default_gpio = 17
    module = "HC-SR501 or similar"
    description = "Passive infrared motion sensor — triggers on heat/movement"
    use_case = "Motion detection in a room or hallway"
    icon = "eye"
    wiring = [
        {"pin": "VCC", "connect": "5V [pin 2]"},
        {"pin": "GND", "connect": "GND [pin 6]"},
        {"pin": "OUT", "connect": "GPIO 17 [pin 11]"},
    ]
    wiring_note = "PIR modules need 5V power. Adjust the onboard potentiometers for sensitivity and hold time."

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import MotionSensor

        self._on_trigger = on_trigger
        self._on_release = on_release
        self._device = MotionSensor(self.gpio)

        self._device.when_motion = self._handle_trigger
        self._device.when_no_motion = self._handle_release

        self._running = True
        log.info("PIR sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("PIR motion detected")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("PIR motion cleared")
        if self._on_release:
            self._on_release()

    def read_value(self) -> bool | None:
        if self._device is not None:
            return bool(self._device.value)
        try:
            from gpiozero import MotionSensor
            dev = MotionSensor(self.gpio)
            try:
                return bool(dev.value)
            finally:
                dev.close()
        except Exception:
            return None

    def stop(self) -> None:
        if not self._running:
            return
        if self._device:
            self._device.close()
            self._device = None
        self._running = False
        log.info("PIR sensor stopped")
