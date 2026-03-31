"""KY-037 big sound sensor (high sensitivity microphone).

Electret microphone with a comparator circuit.  The digital output
(DO) triggers when ambient sound exceeds the threshold set by the
onboard potentiometer.  Produces brief pulses on loud sounds -
similar to the vibration sensor pattern.

The analog output (AO) is ignored since the Pi has no ADC.

Calibration: pulse_count and pulse_window let you require multiple
loud sounds within a time window before triggering, filtering out
single accidental noises.

Wiring (3 pins - ignore AO):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO      → GPIO [default pin 23]

Note: Adjust the onboard potentiometer to set the sound threshold.
"""

import logging
import threading
import time

from .base import BaseSensor

log = logging.getLogger("sensor.sound_big")


class SoundBigSensor(BaseSensor):
    name = "Sound (Big)"
    sensor_type = "sound_big"
    default_gpio = 23
    module = "KY-037"
    description = "High-sensitivity microphone - triggers on loud sounds"
    use_case = "Glass breaking, door slamming, loud noise detection"
    icon = "zap"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 23 [pin 16]"},
    )
    wiring_note = "Adjust the onboard potentiometer to set the sound trigger threshold. Ignore the AO (analog) pin."
    calibration_schema = (
        {
            "key": "pulse_count",
            "name": "Pulse threshold",
            "type": "range",
            "min": 1,
            "max": 20,
            "default": 1,
            "step": 1,
            "description": "Number of sound pulses required to trigger. Higher values filter out isolated noises.",
            "labels": {"min": "Sensitive", "max": "Firm"},
        },
        {
            "key": "pulse_window",
            "name": "Counting window",
            "type": "range",
            "min": 1,
            "max": 30,
            "default": 5,
            "step": 1,
            "unit": "seconds",
            "description": "Time window to count pulses in. Only used when pulse threshold > 1.",
            "labels": {"min": "1s", "max": "30s"},
        },
    )

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None
        self._pulse_count = kwargs.get("pulse_count", 1)
        self._pulse_window = kwargs.get("pulse_window", 5)
        self._pulse_times: list[float] = []
        self._pulse_lock = threading.Lock()

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        self._pulse_times = []
        # KY-037 DO: normally high, pulses low on loud sound
        self._device = DigitalInputDevice(self.gpio, pull_up=True,
                                          bounce_time=0.1)
        self._device.when_deactivated = self._handle_pulse
        self._device.when_activated = self._handle_release

        self._running = True
        log.info("Sound (big) sensor started on GPIO %d (pulse_count=%d, window=%ds)",
                 self.gpio, self._pulse_count, self._pulse_window)

    def _handle_pulse(self):
        if self._pulse_count <= 1:
            log.info("Sound detected (big mic)")
            if self._on_trigger:
                self._on_trigger()
            return

        now = time.monotonic()
        with self._pulse_lock:
            cutoff = now - self._pulse_window
            self._pulse_times = [t for t in self._pulse_times if t > cutoff]
            self._pulse_times.append(now)
            count = len(self._pulse_times)

        log.debug("Sound pulse %d/%d (big)", count, self._pulse_count)
        if count >= self._pulse_count:
            log.info("Sound threshold reached (%d pulses in %ds, big mic)",
                     self._pulse_count, self._pulse_window)
            with self._pulse_lock:
                self._pulse_times.clear()
            if self._on_trigger:
                self._on_trigger()

    def _handle_release(self):
        log.debug("Sound pulse ended (big)")
        if self._pulse_count <= 1 and self._on_release:
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
        log.info("Sound (big) sensor stopped")
