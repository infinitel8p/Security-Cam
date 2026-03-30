"""KY-031 knock/tap sensor.

Detects taps, knocks, or light impacts via a spring-contact switch.
Similar to KY-002 vibration but tuned for deliberate taps rather
than sustained vibration.  Produces brief pulses - the sensor
manager's hold timeout keeps recording running through repeated knocks.

Wiring (3 pins):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO (S)  → GPIO [default pin 19]
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.knock")


class KnockSensor(BaseSensor):
    name = "Knock / Tap"
    sensor_type = "knock"
    default_gpio = 19
    module = "KY-031"
    description = "Knock sensor - detects taps and deliberate knocks"
    use_case = "Detect knocking on door or tapping on window"
    icon = "zap"
    wiring = [
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO (S)", "connect": "GPIO 19 [pin 35]"},
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
        # KY-031: normally high, pulses low on knock
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.1)
        self._device.when_deactivated = self._handle_trigger
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("Knock sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Knock detected")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.debug("Knock pulse ended")
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
        log.info("Knock sensor stopped")
