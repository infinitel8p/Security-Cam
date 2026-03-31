"""Sensor registry - maps type strings to sensor classes.

Usage:
    from modules.sensors import SENSOR_REGISTRY, create_sensor
    sensor = create_sensor("reed_switch", gpio=22)
"""

from .reed_switch import ReedSwitchSensor
from .pir import PIRSensor
from .button import ButtonSensor
from .mock import MockSensor
from .vibration import VibrationSensor
from .light_gate import LightGateSensor
from .hall_digital import HallDigitalSensor
from .knock import KnockSensor
from .tilt import TiltSensor
from .touch import TouchSensor
from .mini_reed import MiniReedSensor

SENSOR_REGISTRY: dict[str, type] = {
    "reed_switch": ReedSwitchSensor,
    "mini_reed": MiniReedSensor,
    "hall_digital": HallDigitalSensor,
    "pir": PIRSensor,
    "vibration": VibrationSensor,
    "knock": KnockSensor,
    "light_gate": LightGateSensor,
    "tilt": TiltSensor,
    "touch": TouchSensor,
    "button": ButtonSensor,
    "mock": MockSensor,
}


def create_sensor(sensor_type: str, gpio: int | None = None, **kwargs):
    """Factory: instantiate a sensor by type string.

    Raises KeyError if the type is not registered.
    """
    cls = SENSOR_REGISTRY[sensor_type]
    return cls(gpio=gpio, **kwargs)


def available_types() -> list[dict]:
    """Return full metadata for all registered sensor types."""
    return [
        {
            "type": cls.sensor_type,
            "name": cls.name,
            "default_gpio": cls.default_gpio,
            "module": cls.module,
            "description": cls.description,
            "use_case": cls.use_case,
            "icon": cls.icon,
            "wiring": cls.wiring,
            "wiring_note": cls.wiring_note,
            "calibration": cls.calibration_schema,
        }
        for cls in SENSOR_REGISTRY.values()
    ]
