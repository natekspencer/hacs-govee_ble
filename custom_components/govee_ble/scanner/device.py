from __future__ import annotations

import abc
import logging
from struct import unpack_from
from typing import Optional, Type

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .attribute import Battery, Hygrometer, Thermometer
from .helpers import decode_temps, twos_complement

_LOGGER = logging.getLogger(__name__)


class Device(abc.ABC):
    def __init__(
        self, device: BLEDevice, advertisement: Optional[AdvertisementData] = None
    ):
        self._device = device
        if advertisement:
            self.update(device, advertisement)

    @property
    def address(self) -> str:
        return self._device.address

    @property
    def name(self) -> str:
        return self._device.name

    @property
    def rssi(self) -> int:
        return self._device.rssi

    @property
    @abc.abstractmethod
    def model(self):
        raise NotImplementedError()

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
        return str(self.dict())


class UnsupportedDevice(Device):
    pass


class H5074(Device, Thermometer, Hygrometer, Battery):
    """Govee H5074 Bluetooth Thermo-Hygrometer Lite"""

    @property
    def model(self):
        return "H5074"

    def dict(self):
        return {
            "address": self.address,
            "name": self.name,
            "model": self.model,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "battery": self.battery,
        }

    def update(self, device: BLEDevice, advertisement: AdvertisementData):
        self.update_device(device)

        update_data = advertisement.manufacturer_data.get(60552)
        if update_data and len(update_data) == 7:
            temp, hum, batt = unpack_from("<HHB", update_data, 1)
            self._temperature = float(twos_complement(temp) / 100)
            self._humidity = float(hum / 100)
            self._battery = int(batt)


class H5174(Device, Thermometer, Hygrometer, Battery):
    """Govee H5174 Smart Thermo-Hygrometer"""

    @property
    def model(self):
        return "H5174"

    def dict(self):
        return {
            "address": self.address,
            "name": self.name,
            "model": self.model,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "battery": self.battery,
        }

    def update(self, device: BLEDevice, advertisement: AdvertisementData):
        self.update_device(device)

        update_data = advertisement.manufacturer_data.get(1)
        if update_data and len(update_data) == 6:
            packet = int(update_data[2:5].hex(), 16)
            self._temperature = decode_temps(packet)
            self._humidity = float((packet % 1000) / 10)
            self._battery = int(update_data[5])


MODEL_MAP: dict[str, Type[Device]] = {"H5074": H5074, "H5174": H5174}


def determine_known_device(
    device: BLEDevice, advertisement: Optional[AdvertisementData] = None
) -> Optional[Device]:
    model = get_govee_model(device.name)
    if model in MODEL_MAP.keys():
        return MODEL_MAP[model](device, advertisement)
    return None


def get_govee_model(name: str) -> Optional[str]:
    if not name:
        return None
    elif name.startswith(("ihoment_", "Govee_", "Minger_", "GBK_")):
        split = name.split("_")
        return split[1] if len(split) == 3 else None
    elif name.startswith("GVH"):
        split = name.split("_")
        return split[0][2:] if len(split) > 1 else None
    return None
