"""Support for Govee BLE lights."""
from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    COLOR_MODE_RGB,
    DOMAIN as LIGHT_DOMAIN,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_EFFECT,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import (
    CONF_KEEP_ALIVE,
    CONF_LOG_ADVERTISEMENTS,
    CONF_LOG_NOTIFICATIONS,
    DATA_UNSUBSCRIBE,
    DEFAULT_KEEP_ALIVE,
    DEFAULT_LOG_ADVERTISEMENTS,
    DEFAULT_LOG_NOTIFICATIONS,
    DOMAIN,
)
from .helpers import get_scanner
from .scanner import Scanner
from .scanner.device import Device, MulticoloredLight

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list[Entity], bool], None],
) -> None:
    """Set up Govee BLE lights using config entry."""
    scanner = await get_scanner(hass, entry)
    log_notifications = entry.options.get(
        CONF_LOG_NOTIFICATIONS, DEFAULT_LOG_NOTIFICATIONS
    )
    keep_alive = entry.options.get(CONF_KEEP_ALIVE, DEFAULT_KEEP_ALIVE)

    @callback
    def async_add_light(device: Device) -> None:
        """Add BLE Light."""
        entities: list[GoveeMulticoloredLight] = []
        _LOGGER.debug("Adding light for %s", device)

        if isinstance(device, MulticoloredLight):
            entities.append(
                GoveeMulticoloredLight(
                    scanner=scanner,
                    device=device,
                    log_notifications=log_notifications,
                    keep_alive=keep_alive,
                )
            )

        async_add_entities(entities)

    hass.data[DOMAIN][entry.entry_id][DATA_UNSUBSCRIBE].append(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_{entry.entry_id}_add_{LIGHT_DOMAIN}",
            async_add_light,
        )
    )


class GoveeMulticoloredLight(LightEntity):
    """Govee Multicolored Light."""

    def __init__(
        self,
        scanner: Scanner,
        device: MulticoloredLight,
        log_notifications: bool = False,
        keep_alive: bool = False,
    ) -> None:
        self._scanner = scanner
        self._device = device

        self._attr_color_mode = COLOR_MODE_RGB
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device.address)},
            "sw_version": self._device.firmware,
        }
        self._attr_supported_color_modes = {COLOR_MODE_RGB}
        self._attr_supported_features = SUPPORT_BRIGHTNESS | SUPPORT_COLOR
        if device.SCENES:
            self._attr_effect_list = [key for key in device.SCENES.keys()]
            self._attr_supported_features |= SUPPORT_EFFECT

        self._log_notifications = log_notifications
        self._keep_alive = keep_alive

    @property
    def available(self) -> bool:
        """Return if this entity is available."""
        return self._device.connection_attempt < 10

    @property
    def name(self) -> str:
        """Return the name of the light."""
        return self._device.name

    @property
    def should_poll(self) -> bool:
        """Polling needed."""
        return self._device.connection_attempt < 15

    @property
    def force_update(self) -> bool:
        """Force update."""
        return True

    @property
    def effect(self) -> str:
        """Return the current effect."""
        return next(
            (
                key
                for key, value in self._device.SCENES.items()
                if value == self._device.scene
            ),
            None,
        )

    @property
    def is_on(self):
        """Return True if the light is on."""
        return self._device.is_on

    @property
    def brightness(self):
        """Return the brightness of the light between 0..255."""
        return self._device.brightness

    @property
    def rgb_color(self):
        return self._device.rgb_color

    @property
    def unique_id(self) -> str:
        """Return unique id for this entity."""
        return f"{self._device.address}.light"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "connected": self._device.is_connected,
            **(
                {}
                if self._device.is_connected
                else {"connection_attempt": self._device.connection_attempt}
            ),
        }

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        effect = kwargs.get(ATTR_EFFECT, None)
        rgb_color = kwargs.get(ATTR_RGB_COLOR, None)
        brightness = kwargs.get(ATTR_BRIGHTNESS, None)
        if effect:
            await self._device.set_scene(effect)
        if rgb_color:
            await self._device.set_color(rgb_color)
        if brightness:
            await self._device.set_brightness(brightness)
        elif not self._device.is_on:
            await self._device.turn_on()

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        await self._device.turn_off()

    async def async_update(self) -> None:
        """Retrieve the latest data."""
        self.hass.async_create_task(self._device.request_update())

    async def async_added_to_hass(self) -> None:
        @callback
        def _update_callback(_: Device) -> None:
            """Call from dispatcher when state changes."""
            if not self.available:
                _LOGGER.debug("Try to reconnect %s", self.name)
                self.hass.async_create_task(self._device.request_update())

        self.async_on_remove(
            self._scanner.on(
                self._device.address,
                lambda event: _update_callback(event["device"]),
            )
        )

        @callback
        def connected_callback():
            """Callback after device connects."""
            # The scanner occasionally stops after a device connects, so we try to restart it here
            log_advertisements = self.platform.config_entry.options.get(
                CONF_LOG_ADVERTISEMENTS, DEFAULT_LOG_ADVERTISEMENTS
            )
            self.hass.async_create_task(
                self._scanner.start(
                    allow_restart=True, log_advertisements=log_advertisements
                )
            )

        self._device._log_notifications = self._log_notifications
        self._device.register_connected_callback(connected_callback)
        self.hass.async_create_task(self._device.connect(keep_alive=self._keep_alive))

    async def async_will_remove_from_hass(self) -> None:
        await self._device.disconnect()
