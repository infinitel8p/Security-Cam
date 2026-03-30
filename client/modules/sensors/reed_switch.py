"""KY-025 magnetic reed switch sensor.

Detects door open/close via a magnet on GPIO (default pin 22).
When the magnet is removed (door opens), the sensor triggers.
When the magnet returns (door closes), the sensor releases.
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.reed")


class ReedSwitchSensor(BaseSensor):
    name = "Reed Switch"
    sensor_type = "reed_switch"
    default_gpio = 22
    module = "KY-025"
    description = "Magnetic reed switch - triggers when magnet is removed"
    use_case = "Door / window open detection"
    icon = "magnet"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 22 [pin 15]"},
    )
    wiring_note = "The AO (analog output) pin is not used."

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.05)

        # KY-025: magnet present = high (closed), magnet removed = low (open)
        self._device.when_deactivated = self._handle_trigger
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("Reed switch started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Reed switch triggered (door opened)")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("Reed switch released (door closed)")
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
        log.info("Reed switch stopped")
