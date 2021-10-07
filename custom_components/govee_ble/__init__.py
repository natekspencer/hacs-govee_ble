"""Govee Thermometer/Humidity BLE HCI monitor sensor integration."""
import asyncio
import logging

from bleak.exc import BleakError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_EXCLUDE_DEVICES,
    CONF_LOG_ADVERTISEMENTS,
    DATA_UNSUBSCRIBE,
    DEFAULT_EXCLUDE_DEVICES,
    DEFAULT_LOG_ADVERTISEMENTS,
    DOMAIN,
    EVENT_DEVICE_ADDED_TO_REGISTRY,
)
from .helpers import get_scanner, string_to_list
from .scanner import DEVICE_DISCOVERED
from .scanner.device import Device, MulticoloredLight

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light", "sensor", "switch"]
DATA_START_PLATFORM_TASK = "start_platform_task"


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Govee BLE component."""
    hass.data.setdefault(DOMAIN, {})
    return True


@callback
def register_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    dev_reg: device_registry.DeviceRegistry,
    device: Device,
) -> None:
    """Register device in device registry."""
    params = {
        "config_entry_id": entry.entry_id,
        "identifiers": {(DOMAIN, device.address)},
        "name": device.name,
        "model": device.model,
        "manufacturer": "Govee",
    }
    device = dev_reg.async_get_or_create(**params)
    async_dispatcher_send(hass, EVENT_DEVICE_ADDED_TO_REGISTRY, device)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Govee BLE from a config entry."""
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    hass.data[DOMAIN][entry.entry_id].setdefault(DATA_UNSUBSCRIBE, [])

    _, exclude_devices = string_to_list(
        entry.options.get(CONF_EXCLUDE_DEVICES, DEFAULT_EXCLUDE_DEVICES)
    )

    scanner = await get_scanner(hass, entry)
    scanner.ignored_addresses = exclude_devices

    dev_reg = device_registry.async_get(hass)

    if exclude_devices:
        # Devices that are in the device registry that are ignored by the integration can be removed
        stored_devices = device_registry.async_entries_for_config_entry(
            dev_reg, entry.entry_id
        )
        ignored_devices = [{(DOMAIN, address)} for address in exclude_devices]
        for device in stored_devices:
            if device.identifiers in ignored_devices:
                dev_reg.async_remove_device(device.id)

    @callback
    def async_on_device_discovered(device: Device) -> None:
        """Handle device discovered event."""
        _LOGGER.debug("Processing device %s", device)

        # register (or update) device in device registry
        register_device(hass, entry, dev_reg, device)

        if isinstance(device, MulticoloredLight):
            async_dispatcher_send(
                hass,
                f"{DOMAIN}_{entry.entry_id}_add_light",
                device,
            )

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

        log_advertisements = entry.options.get(
            CONF_LOG_ADVERTISEMENTS, DEFAULT_LOG_ADVERTISEMENTS
        )

        try:
            await scanner.start(log_advertisements=log_advertisements)
        except BleakError as ex:
            _LOGGER.error("Cancelling start platforms: %s", ex)
        # except Exception as ex:
        #     _LOGGER.exception("Unexpected exception: %s", ex)

    platform_task = hass.async_create_task(start_platforms())
    hass.data[DOMAIN][entry.entry_id][DATA_START_PLATFORM_TASK] = platform_task

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    info = hass.data[DOMAIN].get(entry.entry_id, None)
    if not info:
        return True

    scanner = await get_scanner(hass, entry)
    devices_stopped = all(
        await asyncio.gather(
            *[
                device.disconnect()
                for device in scanner.known_devices
                if isinstance(device, MulticoloredLight)
            ]
        )
    )
    await scanner.stop()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    hass.data[DOMAIN].pop(entry.entry_id)

    platform_task: asyncio.Task = info[DATA_START_PLATFORM_TASK]
    platform_task.cancel()
    await platform_task

    for unsub in info[DATA_UNSUBSCRIBE]:
        unsub()

    return devices_stopped and unload_ok
