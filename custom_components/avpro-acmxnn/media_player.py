"""Platform for media_player integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity

from . import controller
from .const import DOMAIN

LOGGER = logging.getLogger(__package__)


# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add media_players for passed config_entry in HA."""
    LOGGER.debug("Adding media_player entities.")

    client = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    #for roller in hub.rollers:
    #    new_devices.append(BatterySensor(roller))
    #    new_devices.append(IlluminanceSensor(roller))
    if new_devices:
        async_add_entities(new_devices)

