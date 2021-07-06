from __future__ import annotations

import abc
import logging
from struct import unpack_from
from typing import Optional, Type

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .attribute import Battery, Hygrometer, Thermometer
from .helpers import decode_temperature_and_humidity, get_govee_model, twos_complement

_LOGGER = logging.getLogger(__name__)


class Device(abc.ABC):
    SUPPORTED_MODELS: set[str] = None

    def __init__(
        self, device: BLEDevice, advertisement: Optional[AdvertisementData] = None
    ):
        """Initialize a device."""
        self._device = device
        self._model = get_govee_model(device.name)
        if advertisement:
            self.update(device, advertisement)

    @property
    def address(self) -> str:
        """Return the address of this device."""
        return self._device.address

    @property
    def name(self) -> str:
        """Return the name of this device."""
        return self._device.name

    @property
    def rssi(self) -> int:
        """Return the rssi of this device."""
        return self._device.rssi

    @property
    def model(self):
        """Return the model of this device."""
        return self._model

    @abc.abstractstaticmethod
    def update(self, device: BLEDevice, advertisement: AdvertisementData):
        raise NotImplementedError()

    def update_device(self, device: BLEDevice):
        if self._device != device:
            self._device = device

    @abc.abstractmethod
    def dict():
        raise NotImplementedError()

    def __repr__(self):
        """Return pertinent data about this device."""
        return str(self.dict())


class UnsupportedDevice(Device):
    pass


class ThermoHygrometer(Device, Thermometer, Hygrometer, Battery):
    """Abstract Govee Thermo-Hygrometer Sensor Device."""

    MANUFACTURER_DATA_KEY: int = None
    OFFSET: int = None
    NUMBER_OF_BYTES: int = None

    def dict(self):
        """Return pertinent data about this device."""
        return {
            "address": self.address,
            "name": self.name,
            "model": self.model,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "battery": self.battery,
        }

    def update(self, device: BLEDevice, advertisement: AdvertisementData):
        """Update the device data from an advertisement."""
        self.update_device(device)

        update_data = advertisement.manufacturer_data.get(self.MANUFACTURER_DATA_KEY)
        if update_data and len(update_data) >= self.OFFSET + self.NUMBER_OF_BYTES:
            self.parse(update_data)

    @abc.abstractmethod
    def parse(self, data: bytes) -> None:
        """Parse the data."""
        raise NotImplementedError()


class ThermoHygrometerPacked(ThermoHygrometer):
    """Govee Thermo-Hygrometer Sensor with packed data for Temperature and Humidity."""

    NUMBER_OF_BYTES = 5

    def parse(self, data: bytes) -> None:
        """Parse the data."""
        temp, hum, batt = unpack_from("<HHB", data, self.OFFSET)
        self._temperature = float(twos_complement(temp) / 100)
        self._humidity = float(hum / 100)
        self._battery = int(batt)


class H50TH(ThermoHygrometerPacked):
    """
    Govee H50XX Thermo-Hygrometer Sensor.

    Supported Models:
    - H5051
    - H5052
    - H5053
    - H5071
    - H5074
    """

    SUPPORTED_MODELS = {"H5051", "H5052", "H5053", "H5071", "H5074"}
    MANUFACTURER_DATA_KEY = 60552  # EC88
    OFFSET = 1


class H5179(ThermoHygrometerPacked):
    """
    Govee H5179 Thermo-Hygrometer Sensor.

    Supported Models:
    - H5179
    """

    SUPPORTED_MODELS = {"H5179"}
    MANUFACTURER_DATA_KEY = 34817  # 8801
    OFFSET = 4


class ThermoHygrometerEncoded(ThermoHygrometer):
    """Govee Thermo-Hygrometer Sensor with combined data for Temperature and Humidity."""

    NUMBER_OF_BYTES = 4

    def parse(self, data: bytes) -> None:
        """Parse the data."""
        self._temperature, self._humidity = decode_temperature_and_humidity(
            data[self.OFFSET : self.OFFSET + 3]
        )
        self._battery = int(data[self.OFFSET + 3])


class H507TH(ThermoHygrometerEncoded):
    """
    Govee H5072/5 Thermo-Hygrometer Sensor.

    Supported Models:
    - H5072
    - H5075
    """

    SUPPORTED_MODELS = {"H5072", "H5075"}
    MANUFACTURER_DATA_KEY = 60552  # EC88
    OFFSET = 1


class H51TH(ThermoHygrometerEncoded):
    """
    Govee H51XX Thermo-Hygrometer Sensor.

    Supported Models:
    - H5101
    - H5102
    - H5174
    - H5177
    """

    SUPPORTED_MODELS = {"H5101", "H5102", "H5174", "H5177"}
    MANUFACTURER_DATA_KEY = 1  # 0001
    OFFSET = 2


VALID_CLASSES: set[Type[Device]] = {H50TH, H507TH, H51TH, H5179}
MODEL_MAP = {model: cls for cls in VALID_CLASSES for model in cls.SUPPORTED_MODELS}


def determine_known_device(
    device: BLEDevice, advertisement: Optional[AdvertisementData] = None
) -> Optional[Device]:
    model = get_govee_model(device.name)
    if model in MODEL_MAP:
        return MODEL_MAP[model](device, advertisement)
    elif model and advertisement.manufacturer_data:
        _LOGGER.debug(
            "%s appears to be a Govee %s, but no handler has been created. Consider opening an issue at https://github.com/natekspencer/hacs-govee_ble/issues with the advertisement message from above.",
            device.name,
            model,
        )
    return None
