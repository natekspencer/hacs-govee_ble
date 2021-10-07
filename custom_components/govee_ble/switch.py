"""Support for Govee BLE scanner as a switch."""
from typing import Any, Callable

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .helpers import get_scanner
from .scanner import Scanner


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list[Entity], bool], None],
) -> None:
    """Set up Govee BLE scanner as a switch using config entry."""
    scanner = await get_scanner(hass, entry)
    async_add_entities([ScannerSwitch(scanner=scanner)], True)


class ScannerSwitch(SwitchEntity):
    """Scanner Switch."""

    def __init__(self, scanner: Scanner) -> None:
        """Initialize the sensor."""
        self._scanner = scanner
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "scanner")},
            "name": "Scanner",
        }
        self._attr_icon = "mdi:radar"
        self._attr_name = "Scanner"
        self._attr_should_poll = True
        self._attr_unique_id = f"{DOMAIN}.scanner"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "known_devices": len(self._scanner.known_devices),
            "last_advertisement_received": self._scanner.last_advertisement_received.isoformat()
            if self._scanner.last_advertisement_received
            else None,
        }

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on."""
        return self._scanner.started

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        await self._scanner.start()

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        await self._scanner.stop()
