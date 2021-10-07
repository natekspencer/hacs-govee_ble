"""Support for Govee BLE sensors."""
from __future__ import annotations

import logging
from typing import Callable

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    PRECISION_TENTHS,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.temperature import display_temp

from .const import DATA_UNSUBSCRIBE, DOMAIN
from .helpers import get_scanner
from .scanner import Scanner
from .scanner.attribute import Attribute, Battery, Hygrometer, Thermometer
from .scanner.device import Device

_LOGGER = logging.getLogger(__name__)


# class ScannerSensor(SensorEntity):
#     """Sensor representing the scanner."""

#     def __init__(self, scanner: Scanner) -> None:
#         """Initialize the sensor."""
#         self._scanner = scanner
#         self._attr_device_class = "timestamp"
#         self._attr_device_info = {
#             "identifiers": {(DOMAIN, "scanner")},
#             "name": "Scanner",
#         }
#         self._attr_name = "Scanner"
#         self._attr_should_poll = True
#         self._attr_unique_id = f"{DOMAIN}.scanner"

#     @property
#     def native_value(self):
#         if self._scanner.last_advertisement_received:
#             return self._scanner.last_advertisement_received.isoformat()
#         return None


class BleSensor(SensorEntity):
    def __init__(self, scanner: Scanner, device: Device) -> None:
        self._scanner = scanner
        self._device = device
        self._attr_device_info = {"identifiers": {(DOMAIN, self._device.address)}}

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

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""

        @callback
        def _update_callback(_: Device) -> None:
            """Call from dispatcher when state changes."""
            self.async_schedule_update_ha_state(force_refresh=True)

        self.async_on_remove(
            self._scanner.on(
                self._device.address,
                lambda event: _update_callback(event["device"]),
            )
        )


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
        return display_temp(
            self.hass, self._device.temperature, TEMP_CELSIUS, PRECISION_TENTHS
        )

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self.hass.config.units.temperature_unit

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
        _LOGGER.debug("Adding sensors for %s", device)

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

    # async_add_entities([ScannerSensor(scanner=scanner)], True)
