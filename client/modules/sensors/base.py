"""Abstract base class for all trigger sensors.

Every sensor implementation must subclass BaseSensor and implement
start() and stop().  The manager calls start() with two callbacks:
  on_trigger  - called when the sensor fires  (door opened, motion, button press)
  on_release  - called when the sensor resets (door closed, motion cleared, button released)

Implementations that don't have a meaningful "release" (e.g. PIR with
auto-reset) can simply never call on_release; the sensor manager handles
a configurable hold timeout for that case.
"""

from abc import ABC, abstractmethod


class BaseSensor(ABC):
    """Interface that every trigger sensor must implement."""

    # Human-readable name shown in the UI
    name: str = "Unknown Sensor"
    # Short identifier used in settings / API
    sensor_type: str = "unknown"
    # Default GPIO pin (overridable via settings)
    default_gpio: int = 0

    # Display metadata - override in subclasses
    module: str = ""                  # e.g. "KY-025"
    description: str = ""             # one-line description
    use_case: str = ""                # what it's good for
    icon: str = "wrench"              # icon key for the frontend
    wiring: list[dict] = []           # [{"pin": "VCC", "connect": "3V3 [pin 17]"}, ...]
    wiring_note: str = ""             # optional note shown below the wiring table

    def __init__(self, gpio: int | None = None, **kwargs):
        self.gpio = gpio if gpio is not None else self.default_gpio
        self._on_trigger = None
        self._on_release = None
        self._running = False

    @abstractmethod
    def start(self, on_trigger, on_release) -> None:
        """Begin monitoring the sensor.

        Args:
            on_trigger: Callable invoked when the sensor is triggered.
            on_release: Callable invoked when the sensor is released.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop monitoring and release hardware resources."""
        ...

    @property
    def running(self) -> bool:
        return self._running

    def read_value(self) -> bool | None:
        """Read the current raw GPIO pin state for wiring tests.

        Returns True/False for the digital level, or None if not readable
        (e.g. mock sensor).  Subclasses that use gpiozero should open a
        temporary device if needed.
        """
        return None

    def _read_gpio(self, pull_up: bool = True) -> bool | None:
        """Helper: read raw GPIO value, reusing running device or opening a temp one."""
        device = getattr(self, "_device", None)
        if device is not None:
            return bool(device.value)
        try:
            from gpiozero import DigitalInputDevice
            dev = DigitalInputDevice(self.gpio, pull_up=pull_up)
            try:
                return bool(dev.value)
            finally:
                dev.close()
        except Exception:
            return None

    def describe(self) -> dict:
        """Return a JSON-serialisable description of this sensor."""
        return {
            "type": self.sensor_type,
            "name": self.name,
            "gpio": self.gpio,
            "running": self._running,
        }
