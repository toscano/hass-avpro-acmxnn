"""Support for AVPro AV-MX-nn matrix switches."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

import aiohttp
import asyncio
import async_timeout
import json

from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, WS_STATE_CONNECTED, WS_STATE_DISCONNECTED, WS_STATE_STARTING, WS_STATE_STOPPED, WS_MAX_FAILED_ATTEMPTS

LOGGER = logging.getLogger(__package__)

class Controller:
    """Controller for talking to the AVPro Matrix switch."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Init."""
        self._host = host
        self._session = session
        self._wsState = WS_STATE_STOPPED
        self._wsFailedAttempts = 0
        self._wsTask = None
        self._name = ""
        self._mac = ""
        self._serial = ""
        self._model = ""
        self._port = 23
        self._inputs = []
        self._vOutputs = []
        self._aOutputs = []

    async def async_check_connection(self, connect: bool = False) -> bool:
        LOGGER.debug(f"Testing connection to {self._host}.")

        try:
            url = f"http://{self._host}/do?cmd=status"

            with async_timeout.timeout(10):
                response = await self._session.get(url)

            data = await response.json()
            self._name = data['info']['name']
            self._mac = data['info']['mac']
            self._model = data['info']['modelname']
            self._port = data['info']['rs232telnetport']
            self._serial = data['info']['serialnumber']
            LOGGER.info(f"Found matrix switch named '{self._name}' of model '{self._model}' with mac address '{self._mac}' and serial number '{self._serial}' on {self._host}:{self._port}.")

            portalias = json.loads(data['info']['portalias'])

            self._inputs = []
            for item in portalias['inputsID']:
                self._inputs.append(item['id'])

            self._vOutputs = []
            for item in portalias['outputsVideoID']:
                self._vOutputs.append(item['id'])

            self._aOutputs = []
            for item in portalias['outputsAudioID']:
                self._aOutputs.append(item['id'])

            LOGGER.debug(f" in: {self._inputs}")
            LOGGER.debug(f"out: {self._vOutputs}")
            LOGGER.debug(f"out: {self._aOutputs}")

            if connect:
                self._wsTask = asyncio.create_task(self.async_ws_connect())


            LOGGER.debug("async_check_connections succeeded.")

            return True
        except:
            LOGGER.warn(f"Description request to {self._host} failed.")

        return False

    async def async_ws_connect(self):
        """Open a persistent websocket connection and act on events."""
        try:
            LOGGER.debug("Connecting to websocket")
            self._wsFailedAttempts = 0
            self._wsState = WS_STATE_STARTING

            while self._wsState != WS_STATE_STOPPED:
                await self.async_ws_run()

        except asyncio.CancelledError as error:
            self._wsState = WS_STATE_STOPPED

    async def async_ws_close(self):
        """Close the listening websocket."""
        if self._wsTask is not None:
            LOGGER.debug("Closing websocket")
            self._wsState = WS_STATE_STOPPED
            self._wsTask.cancel()
            self._wsTask = None


    async def async_ws_run(self):

        try:
            if self._session.closed:
                self._wsState = WS_STATE_STOPPED
                LOGGER.info(f"Websocket connect abandoned: Client is closed. We must be shutting down.")
                return

            url = f"ws://{self._host}/ws/uart"
            LOGGER.debug(f"Connecting to {url}")

            async with self._session.ws_connect(url, heartbeat=15, ssl=False) as ws_client:
                self._wsState = WS_STATE_CONNECTED
                self._wsfailed_attempts = 0

                LOGGER.info(f"Connected to {url}")

                async for message in ws_client:
                    if self._wsState == WS_STATE_STOPPED:
                        break

                    if message.type == aiohttp.WSMsgType.TEXT:
                        data = message.data.strip()
                        LOGGER.debug(f"WS TEXT: {data}")

                    elif message.type == aiohttp.WSMsgType.CLOSED:
                        LOGGER.warning("AIOHTTP websocket connection closed")
                        break

                    elif message.type == aiohttp.WSMsgType.ERROR:
                        LOGGER.error("AIOHTTP websocket error")
                        break

        except aiohttp.ClientResponseError as error:
            if error.code == 401:
                LOGGER.error(f"Credentials rejected: {type(error)=}.")
            else:
                LOGGER.error(f"Unexpected response received: {type(error)=}.")

            self._wsState = WS_STATE_STOPPED

        except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as error:

            if self._wsfailed_attempts >= WS_MAX_FAILED_ATTEMPTS:
                self._wsState = WS_STATE_STOPPED
                LOGGER.error("Too many errors.")
            elif self._wsState != WS_STATE_STOPPED:
                retry_delay = min(2 ** (self._wsfailed_attempts - 1) * 30, 300)
                self._wsfailed_attempts += 1
                LOGGER.error(f"Websocket connection failed, retrying in {retry_delay}s: {type(error)=}.")
                self._wsState = WS_STATE_DISCONNECTED
                await asyncio.sleep(retry_delay)
        except Exception as error:  # pylint: disable=broad-except
            if self._wsState != WS_STATE_STOPPED:
                LOGGER.exception(f"Unexpected exception occurred: {type(error)=}.")
                self._wsState = WS_STATE_STOPPED
                await asyncio.sleep(5)


    @property
    def mac(self) -> str:
        return self._mac

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    @property
    def serial(self) -> str:
        return self._serial
