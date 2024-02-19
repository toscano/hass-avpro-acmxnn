"""Support for AVPro AV-MX-nn matrix switches."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .controller import Controller

LOGGER = logging.getLogger(__package__)


class AVProMxFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for AV-MX-nn matrix switches."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self) -> None:
        """Initialize flow."""
        self._host: str | None = None
        self._errors: dict[str, str] = {}

    async def async_validate_input(self) -> FlowResult | None:
        """Validate the input Against the device."""

        self._errors.clear()
        session = async_get_clientsession(self.hass)
        client = Controller(self._host, session)

        if not await client.async_check_connection():
            self._errors["base"] = "cannot_connect"
            LOGGER.error("Cannot connect")
            return None

        await self.async_set_unique_id(client.serial)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=client.name,
            data={CONF_HOST: self._host, CONF_NAME: client.name},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            result = await self.async_validate_input()
            if result is not None:
                return result

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=self._errors,
        )

