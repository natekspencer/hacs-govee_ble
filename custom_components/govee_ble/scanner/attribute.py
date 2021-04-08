from abc import ABC
from dataclasses import dataclass


class Attribute(ABC):
    pass


@dataclass
class Thermometer(Attribute):
    _temperature: float = None

    @property
    def temperature(self):
        return self._temperature


@dataclass
class Hygrometer(Attribute):
    _humidity: float = None

    @property
    def humidity(self):
        return self._humidity


@dataclass
class Battery(Attribute):
    _battery: int = None

    @property
    def battery(self):
        return self._battery
