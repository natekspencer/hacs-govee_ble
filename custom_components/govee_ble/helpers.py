"""Govee BLE Helpers."""
from typing import Optional

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SCANNER
from .scanner import Scanner


async def get_scanner(hass: HomeAssistant, entry: ConfigEntry) -> Scanner:
    scanner = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get(SCANNER, None)
    if not scanner:
        scanner = hass.data[DOMAIN][entry.entry_id][SCANNER] = Scanner()
    return scanner


def string_to_list(
    string: str, schema: Optional[vol.Schema] = None
) -> tuple[bool, list[str]]:
    """Return a comma-separated string as a list."""
    invalid = False
    items = [x.strip() for x in string.split(",") if x.strip()]
    if schema:
        try:
            items = schema(items)
        except vol.Invalid:
            invalid = True

    return invalid, items
