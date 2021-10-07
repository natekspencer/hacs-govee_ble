from abc import ABC
from dataclasses import dataclass
from typing import Optional

from .enums import MusicMode


class Attribute(ABC):
    """Abstract attribute class."""

    pass


@dataclass
class Battery(Attribute):
    """Attributes associated with a battery."""

    _battery: int = None

    @property
    def battery(self) -> int:
        """Return the battery level."""
        return self._battery


@dataclass
class Color(Attribute):
    """Attributes associated with a color."""

    _rgb_color: tuple[int, int, int] = None

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the RGB color value."""
        return self._rgb_color


@dataclass
class DeviceInfo(Attribute):
    """Attributes associated with device info."""

    _firmware: Optional[str] = None
    _hardware: Optional[str] = None

    @property
    def firmware(self) -> Optional[str]:
        """Return the firmware version."""
        return self._firmware

    @property
    def hardware(self) -> Optional[str]:
        """Return the hardware version."""
        return self._hardware


@dataclass
class Hygrometer(Attribute):
    """Attributes associated with a hygrometer."""

    _humidity: float = None

    @property
    def humidity(self) -> float:
        """Return the humidity of the hygrometer."""
        return self._humidity


@dataclass
class Light(Attribute):
    """Attributes associated with a light."""

    __max_brightness: int = 255
    _brightness_scale: int = __max_brightness
    _brightness: int = 0
    _is_on: bool = False

    def _brightness_scaled(self, brightness: int, inverse: bool = False) -> int:
        """Return the scaled brightness of the light."""
        return round(
            brightness
            * (
                (self._brightness_scale / self.__max_brightness)
                if inverse
                else (self.__max_brightness / self._brightness_scale)
            )
        )

    @property
    def brightness(self) -> int:
        """Return the brightness of the light between 0..255."""
        return self._brightness_scaled(self._brightness)

    @property
    def is_on(self) -> bool:
        """Return whether the light is on."""
        return self._is_on


@dataclass
class Mode(Attribute):
    """Attributes associated with a mode."""

    _mode: Optional[int] = None
    _music_mode: Optional[MusicMode] = None
    _scene: Optional[int] = None

    @property
    def mode(self) -> Optional[int]:
        """Return the mode."""
        return self._mode

    @property
    def music_mode(self) -> Optional[MusicMode]:
        """Return the music mode."""
        return self._music_mode

    @property
    def scene(self) -> Optional[int]:
        """Return the scene."""
        return self._scene


@dataclass
class Thermometer(Attribute):
    """Attributes associated with a thermometer."""

    _temperature: float = None

    @property
    def temperature(self) -> float:
        """Return the temperature of the thermometer."""
        return self._temperature
