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
from .const import DOMAIN, OUTPUT_TYPE_AUDIO, OUTPUT_TYPE_VIDEO, WS_STATE_CONNECTED, WS_STATE_DISCONNECTED

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
            new_devices.append( MatrixOutput(hass, entry, client, name, index+1, OUTPUT_TYPE_VIDEO) )

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

        self._sourceIndex = -1
        self._sourceName = ""

        self._attr_unique_id = f"{entry.unique_id}_{output_type}_{index:02d}"
        controller.add_subscriber(self.data_callback)

    def data_callback(self, data: str):

        if data == WS_STATE_CONNECTED or data == WS_STATE_DISCONNECTED:
            LOGGER.debug(f"{self._name} connection state changed to {data}.")
            self.schedule_update_ha_state()
            return

        splits = data.split(' ')
        if splits and len(splits)==3 and splits[0]==f"OUT{self._index}" and splits[1]==f"{self._output_type}S":

            sourceIndex = int(splits[2][2:])-1 # We subtract one since the device reports by one based index
            if (self._sourceIndex != sourceIndex):
                self._sourceIndex = sourceIndex
                self._sourceName = self._controller.video_inputs[sourceIndex]
                LOGGER.debug(f"{self._name}<--{self._sourceName}")
                self.schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self):
        if self._controller.is_online:
            return "mdi:video-switch"
        else:
            return "mdi:video-switch-outline"

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return False

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if self._controller.is_online:
            return MediaPlayerState.ON
        else:
            return MediaPlayerState.OFF

    @property
    def available(self) -> bool:
        """Return if the media player is available."""
        return self._controller.is_online

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return MediaPlayerEntityFeature.SELECT_SOURCE

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return self._sourceName

    @property
    def source_list(self):
        # List of available input sources.
        return self._controller.clean_inputs

    async def async_select_source(self, source):
        # Select input source.
        index = self._controller.video_inputs.index(source)+1
        await self._controller.async_send(f"SET OUT{self._index} {self._output_type}S IN{index}")
