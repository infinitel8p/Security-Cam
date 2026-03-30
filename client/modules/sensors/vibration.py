"""KY-002 vibration/shock sensor.

Detects impact or vibration via a spring-contact switch on GPIO.
Produces brief digital pulses on each vibration - there is no
sustained "triggered" state, so on_release is called immediately
after on_trigger.  The sensor manager's hold timeout keeps the
recording running through repeated vibrations.

Wiring (3 pins - ignore AO if present):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO      → GPIO [default pin 5]
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.vibration")


class VibrationSensor(BaseSensor):
    name = "Vibration / Shock"
    sensor_type = "vibration"
    default_gpio = 5
    module = "KY-002"
    description = "Spring-contact shock sensor - brief pulse on impact"
    use_case = "Door slam, forced entry, impact detection"
    icon = "zap"
    wiring = [
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 5 [pin 29]"},
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
        # KY-002: normally high, pulses low on vibration
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.1)
        self._device.when_deactivated = self._handle_trigger
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("Vibration sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Vibration detected")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.debug("Vibration pulse ended")
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
        log.info("Vibration sensor stopped")
