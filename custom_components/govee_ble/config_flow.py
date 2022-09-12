"""Adds config flow for Govee BLE."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Optional(CONF_NAME, default="Govee BLE"): str})


class GoveeBleFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
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
