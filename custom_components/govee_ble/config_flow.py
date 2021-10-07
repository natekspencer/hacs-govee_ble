"""Adds config flow for Govee BLE."""
from typing import Any, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_EXCLUDE_DEVICES,
    CONF_KEEP_ALIVE,
    CONF_LOG_ADVERTISEMENTS,
    CONF_LOG_NOTIFICATIONS,
    DEFAULT_EXCLUDE_DEVICES,
    DEFAULT_KEEP_ALIVE,
    DEFAULT_LOG_ADVERTISEMENTS,
    DEFAULT_LOG_NOTIFICATIONS,
    DOMAIN,
)
from .helpers import string_to_list

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Optional(CONF_NAME, default="Govee BLE"): str})
EXCLUDE_DEVICES_SCHEMA = vol.Schema(vol.All(cv.ensure_list, [cv.string]))


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Govee BLE."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ):
        """Return the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Govee BLE."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            bad_devices, _ = string_to_list(
                user_input.get(CONF_EXCLUDE_DEVICES, DEFAULT_EXCLUDE_DEVICES),
                EXCLUDE_DEVICES_SCHEMA,
            )

            if not bad_devices:
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self.config_entry.entry_id)
                )
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_EXCLUDE_DEVICES,
                        description={
                            "suggested_value": self.config_entry.options.get(
                                CONF_EXCLUDE_DEVICES, DEFAULT_EXCLUDE_DEVICES
                            )
                        },
                    ): str,
                    vol.Optional(
                        CONF_LOG_ADVERTISEMENTS,
                        default=self.config_entry.options.get(
                            CONF_LOG_ADVERTISEMENTS, DEFAULT_LOG_ADVERTISEMENTS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_LOG_NOTIFICATIONS,
                        default=self.config_entry.options.get(
                            CONF_LOG_NOTIFICATIONS, DEFAULT_LOG_NOTIFICATIONS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_KEEP_ALIVE,
                        default=self.config_entry.options.get(
                            CONF_KEEP_ALIVE, DEFAULT_KEEP_ALIVE
                        ),
                    ): bool,
                }
            ),
        )
