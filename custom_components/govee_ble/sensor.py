"""Support for Govee BLE sensors."""
from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DATA_UNSUBSCRIBE, DOMAIN
from .helpers import get_scanner
from .scanner import Scanner
from .scanner.attribute import Attribute, Battery, Hygrometer, Thermometer
from .scanner.device import Device

_LOGGER = logging.getLogger(__name__)


class BleSensor(Entity):
    def __init__(self, scanner: Scanner, device: Device) -> None:
        self._scanner = scanner
        self._device = device

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._device.name

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def force_update(self) -> bool:
        """Force update."""
        return True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return the device information for this entity."""
        # device is precreated in main handler
        return {"identifiers": {(DOMAIN, self._device.address)}}

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        self.async_on_remove(
            self._scanner.on(
                self._device.address,
                lambda event: self._update_callback(event["device"]),
            )
        )

    @callback
    def _update_callback(self, device: Device) -> None:
        """Call from dispatcher when state changes."""
        self._device = device
        self.async_schedule_update_ha_state(force_refresh=True)


class AddressSensor(BleSensor):
    """Govee BLE Address Sensor"""

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{super().name} Address"

    @property
    def unique_id(self) -> str:
        """Return unique id for this entity."""
        return f"{self._device.address}.address"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._device.address

    @property
    def icon(self):
        """Return the icon for this sensor."""
        return "mdi:bluetooth"


class TemperatureSensor(BleSensor):
    """Govee BLE temperature sensor."""

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{super().name} Temperature"

    @property
    def unique_id(self) -> str:
        """Return unique id for this entity."""
        return f"{self._device.address}.temperature"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._device.temperature

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def device_class(self):
        """Return the unit of measurement."""
        return DEVICE_CLASS_TEMPERATURE


class HumiditySensor(BleSensor):
    """Govee BLE humidity sensor."""

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{super().name} Humidity"

    @property
    def unique_id(self) -> str:
        """Return unique id for this entity."""
        return f"{self._device.address}.humidity"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._device.humidity

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return PERCENTAGE

    @property
    def device_class(self):
        """Return the unit of measurement."""
        return DEVICE_CLASS_HUMIDITY


class BatterySensor(BleSensor):
    """Govee BLE battery sensor."""

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{super().name} Battery"

    @property
    def unique_id(self) -> str:
        """Return unique id for this entity."""
        return f"{self._device.address}.battery"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._device.battery

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return PERCENTAGE

    @property
    def device_class(self):
        """Return the unit of measurement."""
        return DEVICE_CLASS_BATTERY


GOVEE_SENSORS: list[tuple[BleSensor, Attribute]] = [
    (AddressSensor, Device),
    (TemperatureSensor, Thermometer),
    (HumiditySensor, Hygrometer),
    (BatterySensor, Battery),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list[Entity], bool], None],
) -> None:
    """Set up Govee BLE sensors using config entry."""
    scanner = await get_scanner(hass, entry)

    @callback
    def async_add_sensor(device: Device) -> None:
        """Add BLE Sensor."""
        entities: list[BleSensor] = []
        _LOGGER.debug("adding sensors for %s", device)

        for sensor_class, attribute in GOVEE_SENSORS:
            if isinstance(device, attribute):
                entities.append(sensor_class(scanner=scanner, device=device))

        async_add_entities(entities)

    hass.data[DOMAIN][entry.entry_id][DATA_UNSUBSCRIBE].append(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_{entry.entry_id}_add_{SENSOR_DOMAIN}",
            async_add_sensor,
        )
    )
