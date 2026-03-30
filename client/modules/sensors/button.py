"""Simple push-button sensor.

Triggers on button press, releases on button release.
Useful for testing or as a manual hardware trigger.
Uses internal pull-up by default (wire button between GPIO and GND).
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.button")


class ButtonSensor(BaseSensor):
    name = "Button"
    sensor_type = "button"
    default_gpio = 27
    module = "Momentary push button"
    description = "Simple push button - triggers on press, releases on release"
    use_case = "Manual hardware trigger or testing"
    icon = "circle"
    wiring = [
        {"pin": "Pin 1", "connect": "GPIO 27 [pin 13]"},
        {"pin": "Pin 2", "connect": "GND [pin 14]"},
    ]
    wiring_note = "No external resistor needed - the software enables an internal pull-up. Wire between GPIO and GND."

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import Button

        self._on_trigger = on_trigger
        self._on_release = on_release
        self._device = Button(self.gpio, pull_up=True, bounce_time=0.05)

        self._device.when_pressed = self._handle_trigger
        self._device.when_released = self._handle_release

        self._running = True
        log.info("Button sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Button pressed")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("Button released")
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
        log.info("Button sensor stopped")
