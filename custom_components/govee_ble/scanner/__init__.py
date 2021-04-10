from __future__ import annotations

import asyncio
import logging
from typing import Callable, Dict, List, Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .device import Device, determine_known_device
from .helpers import log_advertisement_message

_LOGGER = logging.getLogger(__name__)

DEVICE_DISCOVERED = "device discovered"


class Scanner:
    def __init__(self) -> None:
        """Initialize the scanner."""
        self.__scanner = BleakScanner()
        self._listeners: Dict[str, List[Callable]] = {}
        self._known_devices: dict[str, Device] = {}

    @property
    def known_devices(self) -> list[Device]:
        return list(self._known_devices.values())

    def on(self, event_name: str, callback: Callable) -> Callable:
        """Register an event callback."""
        listeners: list = self._listeners.setdefault(event_name, [])
        listeners.append(callback)

        def unsubscribe() -> None:
            """Unsubscribe listeners."""
            if callback in listeners:
                listeners.remove(callback)

        return unsubscribe

    def emit(self, event_name: str, data: dict) -> None:
        """Run all callbacks for an event."""
        for listener in self._listeners.get(event_name, []):
            listener(data)

    async def start(self):
        def _callback(device: BLEDevice, advertisement: AdvertisementData):
            log_advertisement_message(device, advertisement)
            known_device = self._known_devices.get(device.address)
            if known_device:
                known_device.update(device=device, advertisement=advertisement)
                self.emit(device.address, {"device": known_device})
            else:
                known_device = determine_known_device(
                    device=device, advertisement=advertisement
                )
                if known_device:
                    self._known_devices[device.address] = known_device
                    self.emit(DEVICE_DISCOVERED, {"device": known_device})

        self.__scanner.register_detection_callback(_callback)
        await self.__scanner.start()

    async def stop(self):
        await self.__scanner.stop()

    @staticmethod
    async def find_known_device_by_address(
        device_identifier: str, timeout: float = 10.0
    ) -> Optional[Device]:
        """Find a device (with metadata) by Bluetooth address or UUID address (macOS)."""
        device_identifier = device_identifier.lower()
        stop_scanning_event = asyncio.Event()

        def stop_if_detected(device: BLEDevice, advertisement: AdvertisementData):
            if device.address.lower() == device_identifier and determine_known_device(
                device, advertisement
            ):
                stop_scanning_event.set()

        async with BleakScanner(
            timeout=timeout, detection_callback=stop_if_detected
        ) as scanner:
            try:
                await asyncio.wait_for(stop_scanning_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                return None
            device = next(
                determine_known_device(d)
                for d in await scanner.get_discovered_devices()
                if d.address.lower() == device_identifier
            )
            return device
