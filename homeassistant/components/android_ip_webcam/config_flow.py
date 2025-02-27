"""Config flow for Android IP Webcam integration."""
from __future__ import annotations

from typing import Any

from pydroid_ipcam import PyDroidIPCam
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Inclusive(CONF_USERNAME, "authentication"): str,
        vol.Inclusive(CONF_PASSWORD, "authentication"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> bool:
    """Validate the user input allows us to connect."""

    websession = async_get_clientsession(hass)
    cam = PyDroidIPCam(
        websession,
        data[CONF_HOST],
        data[CONF_PORT],
        username=data.get(CONF_USERNAME),
        password=data.get(CONF_PASSWORD),
        ssl=False,
    )
    await cam.update()
    return cam.available


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Android IP Webcam."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        self._async_abort_entries_match(
            {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
        )
        # to be removed when YAML import is removed
        title = user_input.get(CONF_NAME) or user_input[CONF_HOST]
        if await validate_input(self.hass, user_input):
            return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors={"base": "cannot_connect"},
        )

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Import a config entry from configuration.yaml."""
        import_config.pop(CONF_SCAN_INTERVAL)
        import_config.pop(CONF_TIMEOUT)
        return await self.async_step_user(import_config)
