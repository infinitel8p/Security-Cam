"""KY-024 linear Hall-effect magnetic sensor (digital mode).

Similar to the KY-003 but includes a potentiometer to adjust the
magnetic field threshold for the digital output.  Also has an analog
output (AO) which we ignore since the Pi has no ADC.

Triggers when the magnetic field drops below the threshold (magnet
removed), releases when the field returns (magnet brought near).

Wiring (3 pins - ignore AO):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO      → GPIO [default pin 12]

Note: Adjust the onboard potentiometer to set the trigger threshold.
"""

import logging

from .base import BaseSensor

log = logging.getLogger("sensor.hall_linear")


class HallLinearSensor(BaseSensor):
    name = "Hall Magnetic (Linear)"
    sensor_type = "hall_linear"
    default_gpio = 12
    module = "KY-024"
    description = "Linear Hall sensor with adjustable threshold - detects magnetic field"
    use_case = "Door / window detection (adjustable sensitivity via potentiometer)"
    icon = "magnet"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 12 [pin 32]"},
    )
    wiring_note = "Adjust the onboard potentiometer to set the magnetic field trigger threshold. Ignore the AO (analog) pin."

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        # DO goes high when field drops below threshold (magnet removed)
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.05)
        self._device.when_activated = self._handle_trigger
        self._device.when_deactivated = self._handle_release

        self._running = True
        log.info("Hall linear sensor started on GPIO %d", self.gpio)

    def _handle_trigger(self):
        log.info("Hall linear: magnet removed (triggered)")
        if self._on_trigger:
            self._on_trigger()

    def _handle_release(self):
        log.info("Hall linear: magnet detected (released)")
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
        log.info("Hall linear sensor stopped")
