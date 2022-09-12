"""Govee Thermometer/Humidity BLE HCI monitor sensor integration."""
from __future__ import annotations

import asyncio
import logging

from bleak.exc import BleakError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, EVENT_DEVICE_ADDED_TO_REGISTRY
from .helpers import get_scanner
from .scanner import DEVICE_DISCOVERED
from .scanner.device import Device

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]
DATA_START_PLATFORM_TASK = "start_platform_task"


@callback
def register_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    dev_reg: device_registry.DeviceRegistry,
    device: Device,
) -> None:
    """Register device in device registry."""
    params = DeviceInfo(
        identifiers={(DOMAIN, device.address)},
        name=device.name,
        model=device.model,
        manufacturer="Govee",
    )

    device = dev_reg.async_get_or_create(config_entry_id=entry.entry_id, **params)

    async_dispatcher_send(hass, EVENT_DEVICE_ADDED_TO_REGISTRY, device)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Govee Thermometer/Humidity BLE from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}

    scanner = await get_scanner(hass, entry)
    dev_reg = await device_registry.async_get_registry(hass)

    @callback
    def async_on_device_discovered(device: Device) -> None:
        """Handle device discovered event."""
        _LOGGER.debug("Processing device %s", device)

        # register (or update) device in device registry
        register_device(hass, entry, dev_reg, device)

        async_dispatcher_send(
            hass,
            f"{DOMAIN}_{entry.entry_id}_add_sensor",
            device,
        )

    async def start_platforms() -> None:
        """Start platforms and perform discovery."""
        # wait until all required platforms are ready
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_setup(entry, platform)
                for platform in PLATFORMS
            ]
        )

        # listen for new devices being discovered
        scanner.on(
            DEVICE_DISCOVERED, lambda event: async_on_device_discovered(event["device"])
        )

        try:
            await scanner.start()
        except BleakError as ex:
            _LOGGER.debug("Cancelling start platforms")
            raise ConfigEntryNotReady from ex

    platform_task = hass.async_create_task(start_platforms())
    hass.data[DOMAIN][entry.entry_id][DATA_START_PLATFORM_TASK] = platform_task

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    scanner = await get_scanner(hass, entry)
    await scanner.stop()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if not unload_ok:
        return False

    info = hass.data[DOMAIN].pop(entry.entry_id)

    platform_task: asyncio.Task = info[DATA_START_PLATFORM_TASK]
    platform_task.cancel()
    await platform_task

    return True
