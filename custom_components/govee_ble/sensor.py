"""Support for Govee BLE sensors."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .helpers import get_scanner
from .scanner import Scanner
from .scanner.attribute import Attribute, Battery, Hygrometer, Thermometer
from .scanner.device import Device

_LOGGER = logging.getLogger(__name__)


@dataclass
class GoveeBleSensorEntityDescription(SensorEntityDescription):
    """A class that describes Govee BLE sensor entities."""

    attribute: Attribute | None = None


GOVEE_SENSORS: tuple[GoveeBleSensorEntityDescription, ...] = (
    GoveeBleSensorEntityDescription(
        key="address",
        name="Address",
        icon="mdi:bluetooth",
        entity_category=EntityCategory.DIAGNOSTIC,
        attribute=Device,
    ),
    GoveeBleSensorEntityDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        attribute=Thermometer,
    ),
    GoveeBleSensorEntityDescription(
        key="humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        attribute=Hygrometer,
    ),
    GoveeBleSensorEntityDescription(
        key="battery",
        name="Battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        attribute=Battery,
    ),
)


class GoveeBleSensorEntity(SensorEntity):
    """Govee Ble sensor entity."""

    _attr_should_poll = False
    _attr_force_update = False

    def __init__(
        self,
        scanner: Scanner,
        device: Device,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize a Govee BLE sensor entity."""
        self._scanner = scanner
        self._device = device
        self.entity_description = entity_description

        self._attr_name = f"{device.name} {entity_description.name}"
        self._attr_unique_id = f"{device.address}.{entity_description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device.address)})

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return getattr(self._device, self.entity_description.key, None)

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
        self.async_schedule_update_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee BLE sensors using config entry."""
    scanner = await get_scanner(hass, entry)

    @callback
    def async_add_sensor(device: Device) -> None:
        """Add BLE Sensor."""
        _LOGGER.debug("Adding sensors for %s", device)
        async_add_entities(
            [
                GoveeBleSensorEntity(
                    scanner=scanner, device=device, entity_description=sensor
                )
                for sensor in GOVEE_SENSORS
                if isinstance(device, sensor.attribute)
            ]
        )

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_{entry.entry_id}_add_{SENSOR_DOMAIN}",
            async_add_sensor,
        )
    )
