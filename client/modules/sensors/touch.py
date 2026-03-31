"""KY-036 metal touch sensor.

Capacitive touch sensor that triggers when a person touches the
metal contact pad.  Useful for detecting if someone touches the
camera housing or a conductive surface near it.

Calibration: touch_duration requires the touch to be held for a
minimum time before triggering, filtering out accidental brushes
and static discharge.

Wiring (3 pins - ignore AO if present):
  + (VCC) → 3V3 [pin 17]
  GND     → GND  [pin 14]
  DO      → GPIO [default pin 16]
"""

import logging
import threading

from .base import BaseSensor

log = logging.getLogger("sensor.touch")


class TouchSensor(BaseSensor):
    name = "Touch Sensor"
    sensor_type = "touch"
    default_gpio = 16
    module = "KY-036"
    description = "Capacitive metal touch sensor - triggers on skin contact"
    use_case = "Detect touching of camera housing or door handle"
    icon = "hand"
    wiring = (
        {"pin": "+ (VCC)", "connect": "3V3 [pin 17]"},
        {"pin": "GND", "connect": "GND [pin 14]"},
        {"pin": "DO", "connect": "GPIO 16 [pin 36]"},
    )
    calibration_schema = (
        {
            "key": "touch_duration",
            "name": "Touch duration",
            "type": "range",
            "min": 0,
            "max": 30,
            "default": 3,
            "step": 1,
            "description": "How long the touch must be held before triggering (in tenths of a second). Filters out accidental brushes.",
            "labels": {"min": "Instant", "max": "3s"},
        },
    )

    def __init__(self, gpio: int | None = None, **kwargs):
        super().__init__(gpio, **kwargs)
        self._device = None
        # touch_duration stored as tenths of a second (0-30 → 0.0-3.0s)
        self._touch_duration = kwargs.get("touch_duration", 3) / 10.0
        self._hold_timer: threading.Timer | None = None

    def start(self, on_trigger, on_release) -> None:
        if self._running:
            return

        from gpiozero import DigitalInputDevice

        self._on_trigger = on_trigger
        self._on_release = on_release
        self._hold_timer = None
        # KY-036: low normally, goes high on touch
        self._device = DigitalInputDevice(self.gpio, pull_up=False,
                                          bounce_time=0.05)
        self._device.when_activated = self._handle_raw_trigger
        self._device.when_deactivated = self._handle_raw_release

        self._running = True
        log.info("Touch sensor started on GPIO %d (touch_duration=%.1fs)",
                 self.gpio, self._touch_duration)

    def _handle_raw_trigger(self):
        """Raw GPIO trigger - start hold timer or fire immediately."""
        if self._touch_duration <= 0:
            log.info("Touch detected")
            if self._on_trigger:
                self._on_trigger()
            return

        log.debug("Touch detected, waiting %.1fs to confirm", self._touch_duration)
        self._cancel_hold_timer()
        self._hold_timer = threading.Timer(self._touch_duration, self._confirmed)
        self._hold_timer.daemon = True
        self._hold_timer.start()

    def _confirmed(self):
        """Called after touch_duration if finger is still held."""
        log.info("Touch held for %.1fs - triggering", self._touch_duration)
        self._hold_timer = None
        if self._on_trigger:
            self._on_trigger()

    def _handle_raw_release(self):
        """Raw GPIO release - cancel hold timer if pending, else fire release."""
        if self._hold_timer is not None:
            log.debug("Touch released before duration threshold - ignoring")
            self._cancel_hold_timer()
            return

        log.info("Touch released")
        if self._on_release:
            self._on_release()

    def _cancel_hold_timer(self):
        if self._hold_timer is not None:
            self._hold_timer.cancel()
            self._hold_timer = None

    def read_value(self) -> bool | None:
        return self._read_gpio(pull_up=False)

    def stop(self) -> None:
        if not self._running:
            return
        self._cancel_hold_timer()
        if self._device:
            self._device.close()
            self._device = None
        self._running = False
        log.info("Touch sensor stopped")
