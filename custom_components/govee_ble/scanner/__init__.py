from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Callable, Dict, List, Optional

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakDBusError

from .device import Device, determine_known_device
from .helpers import log_advertisement_message

_LOGGER = logging.getLogger(__name__)

DEVICE_DISCOVERED = "device discovered"


class Scanner:
    """Scanner class."""

    def __init__(self) -> None:
        """Initialize the scanner."""
        self.__scanner = BleakScanner()
        self._listeners: Dict[str, List[Callable]] = {}
        self._known_devices: dict[str, Device] = {}
        self.started = False
        self.last_advertisement_received: datetime = None
        self.ignored_addresses: list[str] = []

    @property
    def known_devices(self) -> list[Device]:
        """Return the list of known devices."""
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

    async def start(
        self, allow_restart: bool = False, log_advertisements: bool = False
    ) -> None:
        """Start scanning for devices.

        log_advertisements (bool): If set to `True`, log received advertisement messages. Defaults to `False`.
        """
        if self.started:
            if not allow_restart:
                _LOGGER.warning(
                    "Scanner is already started. If you wish to force a restart, pass `allow_restart = True` to the start method"
                )
                return
            await self.stop()

        def _callback(device: BLEDevice, advertisement: AdvertisementData) -> None:
            """Callback on device detection."""
            self.last_advertisement_received = datetime.now(timezone.utc)
            if device.address in self.ignored_addresses:
                return
            if log_advertisements:
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
        self.started = True
        _LOGGER.debug("Scanner started")

    async def stop(self) -> None:
        """Stop scanning for devices."""
        if not self.started:
            return

        try:
            await self.__scanner.stop()
        except BleakDBusError as ex:
            if not (
                ex.dbus_error == "org.bluez.Error.Failed"
                and ex.dbus_error_details == "No discovery started"
            ):
                raise

        self.started = False
        _LOGGER.debug("Scanner stopped")

    @staticmethod
    async def find_known_device_by_address(
        device_identifier: str, timeout: float = 10.0
    ) -> Optional[Device]:
        """Find a device (with metadata) by Bluetooth (or UUID, if macOS) address."""
        device_identifier = device_identifier.lower()
        stop_scanning_event = asyncio.Event()

        def stop_if_detected(
            device: BLEDevice, advertisement: AdvertisementData
        ) -> None:
            """Stop scanning once the device being searched for is found."""
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
            found_device = next(
                determine_known_device(device)
                for device in scanner.discovered_devices
                if device.address.lower() == device_identifier
            )
            return found_device
