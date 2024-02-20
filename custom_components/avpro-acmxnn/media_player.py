"""Platform for media_player integration."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity

from . import controller
from .const import DOMAIN, OUTPUT_TYPE_AUDIO, OUTPUT_TYPE_VIDEO

LOGGER = logging.getLogger(__package__)


# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Add media_players for passed config_entry in HA."""
    LOGGER.debug("Adding media_player entities.")

    client = hass.data[DOMAIN][entry.entry_id]

    new_devices = []

    for index, name in enumerate(client.video_outputs):
        # we skip video outputs without a name or those whose name starts with a dot (.)
        if name.strip() and name[0] != '.':
            LOGGER.debug(f"Found video output[{index}]={name}")
            new_devices.append( MatrixOutput(hass, entry, client, name, index, OUTPUT_TYPE_VIDEO) )

    if new_devices:
        async_add_entities(new_devices)

    await client.async_get_status()


class MatrixOutput(MediaPlayerEntity):
    """Our Media Player"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, controller: controller.Controller, name: str, index: int, output_type: str):
        """Initialize our Media Player"""
        self._hass = hass
        self._controller = controller
        self._index = index
        self._name = name
        self._output_type = output_type

        self._attr_unique_id = f"{entry.unique_id}_{output_type}_{index:02d}"


    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self):
        return "mdi:video-switch" # "video-switch-outline"

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return False

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        return MediaPlayerState.ON

    @property
    def available(self) -> bool:
        """Return if the media player is available."""
        return True

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return MediaPlayerEntityFeature.SELECT_SOURCE

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return "Roku"

    @property
    def source_list(self):
        # List of available input sources.

        return ["Roku", "Fire TV", "Laser Disc"]
