"""Govee BLE Helpers."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SCANNER
from .scanner import Scanner


async def get_scanner(hass: HomeAssistant, entry: ConfigEntry) -> Scanner:
    """Get an instance of the scanner."""
    scanner = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get(SCANNER, None)
    if not scanner:
        scanner = hass.data[DOMAIN][entry.entry_id][SCANNER] = Scanner()
    return scanner
