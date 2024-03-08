"""Platform for media_player integration."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    ATTR_TO_PROPERTY
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity

from . import controller
from .const import DOMAIN, MANUFACTURER, OUTPUT_TYPE_AUDIO, OUTPUT_TYPE_VIDEO, WS_STATE_CONNECTED, WS_STATE_DISCONNECTED

LOGGER = logging.getLogger(__package__)

VIDEO_MODES = ["AUTO", "BYPASS", "4K->2K", "2K->4K", "HDBT C Mode"]
AUDIO_DELAYS = ["0ms","90ms","180ms","270ms","360ms","450ms","540ms","630ms"]

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

    for index, name in enumerate(client.audio_outputs):
        # we skip video outputs without a name or those whose name starts with a dot (.)
        if name.strip() and name[0] != '.':
            LOGGER.debug(f"Found audio output[{index}]={name}")
            new_devices.append( MatrixOutput(hass, entry, client, name, index+1, OUTPUT_TYPE_AUDIO) )

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
        self._extra_attributes = {}
        self._isOn = True

        if (output_type== OUTPUT_TYPE_VIDEO):
            self._name = f"{name} HDMI"
        elif (output_type== OUTPUT_TYPE_AUDIO):
            self._name = f"{name} audio"
        else:
            self._name = name

        self._output_type = output_type

        self._sourceIndex = -1
        self._sourceName = ""

        self._attr_unique_id = f"{entry.unique_id}_{output_type}_{index:02d}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            manufacturer=MANUFACTURER,
            model=self._controller.model,
            name=entry.data[CONF_NAME],
            sw_version=self._controller.version,
        )

        controller.add_subscriber(self.data_callback)

    def data_callback(self, data: str):

        if data == WS_STATE_CONNECTED or data == WS_STATE_DISCONNECTED:
            LOGGER.debug(f"{self._name} connection state changed to {data}.")
            self._extra_attributes = {}
            self.update_ha()
            return

        splits = data.split(' ')
        if splits and len(splits)==2 and splits[0]=="EXAMX":
            self.update_ha()
            return

        if splits and len(splits)>0 and splits[0]==f"IN{self._sourceIndex+1}":
            self.update_ha()

        elif splits and len(splits)>0 and splits[0]==f"OUT{self._index}":

            # OUTx [V|A]S INy
            if len(splits)==3  and splits[1]==f"{self._output_type}S":
                sourceIndex = int(splits[2][2:])-1 # We subtract one since the device reports by one based index
                if (self._sourceIndex != sourceIndex):
                    self._sourceIndex = sourceIndex
                    self._sourceName = self._controller.video_inputs[sourceIndex]
                    LOGGER.debug(f"{self._name}<--{self._sourceName}")
                    self._attr_app_name = self._sourceName
                    self.update_ha()

            # OUTx VIDEOy
            elif len(splits)==2 and splits[1][0:5]=="VIDEO":
                vmode = int(splits[1][5:])
                if (vmode>=0 and vmode<=4):
                    self._extra_attributes["video_mode"]=VIDEO_MODES[vmode]
                    LOGGER.debug(f"{self._name}<--{VIDEO_MODES[vmode]}")
                    self.update_ha()

            # OUTx EXADL PHy == OUT1 EXADL PH0
            elif len(splits)==3 and splits[1]=="EXADL":
                delayIndex = int(splits[2][2:])
                if (delayIndex>=0 and delayIndex<=7):
                    self._extra_attributes["audio_delay"]=AUDIO_DELAYS[delayIndex]
                    LOGGER.debug(f"{self._name}<--{AUDIO_DELAYS[delayIndex]}")
                    self.update_ha()

            # OUTx STREAM ON/OFF
            elif len(splits)==3 and splits[1]=="STREAM":
                self._isOn = (splits[2]=="ON")
                LOGGER.debug(f"{self._name}<--{splits[2]}")
                self.update_ha()

            ## OUTx IMAGE ENH y
            ## OUTx EXA EN/DIS
            ## OUTx SGM EN/DIS

            #OUT1 EXA EN
            #OUT1 EXA LVL10
            #OUT1 EXA RVL10
            #OUT1 EXAUD LEV100
            #OUT1 EXEQ MODE0
            #OUT1 SGMT 0


    def update_ha(self):
        try:
            self.schedule_update_ha_state()
        except Exception as error:  # pylint: disable=broad-except
            LOGGER.debug("State update failed.")

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
        if self._isOn:
            return MediaPlayerState.ON
        else:
            return MediaPlayerState.OFF

    @property
    def available(self) -> bool:
        """Return if the media player is available."""
        if self._output_type == OUTPUT_TYPE_AUDIO and self._controller.matrix_audio == False:
            return False

        return self._controller.is_online

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return MediaPlayerEntityFeature.SELECT_SOURCE | MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF

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

    async def async_turn_on(self):
        # Turn the media player on.
        await self._controller.async_send(f"SET OUT{self._index} STREAM ON")

        # Reset our input signal please
        if self._sourceIndex != -1:
            await self._controller.async_send(f"A00 SET IN{self._sourceIndex} RST")

    async def async_turn_off(self):
        await self._controller.async_send(f"SET OUT{self._index} STREAM OFF")

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        if self._isOn:
            self._extra_attributes['input_index']=self._sourceIndex+1
            self._extra_attributes['input_has_signal']= (self._controller._inputSignals[self._sourceIndex]==1)
        else:
            self._extra_attributes['input_index']=0
            self._extra_attributes['input_has_signal']= False

        # Useful for making sensors
        return self._extra_attributes