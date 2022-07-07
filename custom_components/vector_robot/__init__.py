"""Base definition of DDL Vector."""
# pylint: disable=unused-argument
from __future__ import annotations
import asyncio

import logging
import random
from datetime import datetime, timedelta
from enum import IntEnum
from functools import partial
from typing import Optional, cast

import pytz
from ha_vector.events import Events
from ha_vector.exceptions import VectorConnectionException
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_NAME, CONF_PASSWORD, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.loader import async_get_integration

from ha_vector.robot import AsyncRobot
from .api_override.robot import Robot
from .const import (
    ATTR_MESSAGE,
    ATTR_USE_VECTOR_VOICE,
    BATTERYMAP_TO_STATE,
    CONF_IP,
    CONF_SERIAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_GOTO_CHARGER,
    SERVICE_LEAVE_CHARGER,
    SERVICE_SPEAK,
    STARTUP,
    STATE_CUBE_BATTERY_LEVEL,
    STATE_CUBE_BATTERY_VOLTS,
    STATE_CUBE_FACTORY_ID,
    STATE_CUBE_LAST_CONTACT,
    STATE_FIRMWARE_VERSION,
    STATE_ROBOT_BATTERY_LEVEL,
    STATE_ROBOT_BATTERY_VOLTS,
    STATE_ROBOT_IS_CHARGNING,
    STATE_ROBOT_IS_ON_CHARGER,
    STATE_ROBOT_SUGGESTED_CHARGE,
    UPDATE_SIGNAL,
)
from .helpers.storage import VectorStore
from .schemes import TTS
from .states import VectorStates
from .vector_utils import DataRunner

# Vector-A6S1
# 00908e7e
# 192.168.1.223


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up cloud API connector from a config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP, integration.version)
    _LOGGER.debug("Entry data: %s", entry.data)
    _LOGGER.debug("Entry options: %s", entry.options)
    _LOGGER.debug("Entry unique ID: %s", entry.unique_id)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": None,
        "listener": None,
    }
    store = VectorStore(hass, entry.data[CONF_NAME])
    config = cast(Optional[dict], await store.async_load())
    dataset = DataRunner(hass, store.path)
    await dataset.async_refresh()

    coordinator = VectorDataUpdateCoordinator(hass, entry, config, dataset.path)
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    await check_unique_id(hass, entry)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN][entry.entry_id]["listener"]()
        hass.data[DOMAIN].pop(entry.entry_id)

        return True

    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def check_unique_id(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Check if a device unique ID is set."""
    if not isinstance(entry.unique_id, type(None)):
        return

    new_unique_id = f"{entry.data.get(CONF_NAME)}_{entry.data.get(CONF_SERIAL)}"

    _LOGGER.debug("Setting new unique ID %s", new_unique_id)
    data = {
        CONF_EMAIL: entry.data[CONF_EMAIL],
        CONF_PASSWORD: entry.data[CONF_PASSWORD],
        CONF_NAME: entry.data[CONF_NAME],
        CONF_IP: entry.data[CONF_IP],
        CONF_SERIAL: entry.data[CONF_SERIAL],
    }
    result = hass.config_entries.async_update_entry(
        entry, data=data, unique_id=new_unique_id
    )
    _LOGGER.debug("Update successful? %s", result)


class VectorConnectionState(IntEnum):
    """Class representing Vector Connection State."""

    UNKNOWN = 0
    CONNECTING = 1
    CONNECTED = 2
    DISCONNECTING = 3
    DISCONNECTED = 4


class VectorDataUpdateCoordinator(DataUpdateCoordinator[Optional[datetime]]):
    """Defines a Vector data update coordinator."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, config: dict, dataset_path: str
    ) -> None:
        """Initialize the connection."""
        self.hass = hass
        self._config_data = entry.data
        self.friendly_name = self._config_data[CONF_NAME]
        self.entry_id = entry.entry_id
        self.serial = self._config_data[CONF_SERIAL]
        self.name = self._config_data[CONF_NAME]
        self.full_name = (
            f"{self._config_data[CONF_NAME]}_{self._config_data[CONF_SERIAL]}"
        )
        self._config = config
        self._dataset = dataset_path

        self.robot = Robot(
            self.serial,
            behavior_control_level=None,
            cache_animation_lists=False,
            enable_face_detection=True,
            estimate_facial_expression=True,
            enable_audio_feed=True,
            name=self._config_data[CONF_NAME],
            ip_address=self._config_data[CONF_IP],
            config=self._config,
            force_async=True,
        )

        self.states = VectorStates()
        # self.chatter = Chatter(self._dataset)
        # self.chatter.get_text(VectorDatasets.DIALOGS, "cliff")

        try:
            self.robot.connect()
        except Exception as exc:
            raise HomeAssistantError from exc

        ### Subscribe to events
        self.robot.events.subscribe(self._on_robot_wake_word, Events.wake_word)
        self.robot.events.subscribe(self._on_event, Events.robot_state)

        ### Register services
        # TTS / Speak
        self.hass.services.async_register(
            DOMAIN, SERVICE_SPEAK, partial(self.async_tts), schema=TTS
        )
        # Drive onto charger
        self.hass.services.async_register(
            DOMAIN, SERVICE_GOTO_CHARGER, partial(self.async_drive_on_charger)
        )
        # Drive off charger
        self.hass.services.async_register(
            DOMAIN, SERVICE_LEAVE_CHARGER, partial(self.async_drive_off_charger)
        )

        super().__init__(hass, _LOGGER, name=self.name, update_interval=SCAN_INTERVAL)

    async def _on_event(self, robot, event_type, event, done):
        """Generic debug event callback."""
        _LOGGER.debug(
            "Event data:\nRobot: %s\nEvent_type: %s\nEvent: %s",
            robot,
            event_type,
            event,
        )

    async def _on_robot_wake_word(self, robot, event_type, event, done):
        """React to wake word."""

        if event == "wake_word_begin":
            await self.hass.async_add_executor_job(robot.conn.request_control)
            await self.hass.async_add_executor_job(
                robot.behavior.say_text, "You called!"
            )
            await self.hass.async_add_executor_job(robot.conn.release_control)

    async def async_drive_on_charger(self, *args, **kwargs) -> None:
        """Send Vector to the charger."""
        _LOGGER.debug("Asking Vector to go onto the charger")
        await asyncio.wrap_future(self.robot.conn.request_control())
        await asyncio.wrap_future(self.robot.behavior.drive_on_charger())
        await asyncio.wrap_future(self.robot.conn.release_control())

    async def async_drive_off_charger(self, *args, **kwargs) -> None:
        """Send Vector to the charger."""
        _LOGGER.debug("Asking Vector to leave the charger")
        await asyncio.wrap_future(self.robot.conn.request_control())
        await asyncio.wrap_future(self.robot.behavior.drive_off_charger())
        await asyncio.wrap_future(self.robot.conn.release_control())

    async def async_tts(self, service_call: ServiceCall) -> None:
        """Make Vector speak."""
        _LOGGER.debug("Asking Vector to say a text")
        try:
            await asyncio.wrap_future(self.robot.conn.request_control())
            await asyncio.wrap_future(
                self.robot.behavior.say_text(
                    text=service_call.data[ATTR_MESSAGE],
                    use_vector_voice=service_call.data[ATTR_USE_VECTOR_VOICE],
                    duration_scalar=1.0,
                )
            )
            await asyncio.wrap_future(self.robot.conn.release_control())
        except VectorConnectionException:
            _LOGGER.warning("Something happend while sending TTS to Vector :(")

    async def _async_update_data(self) -> datetime | None:
        """Update Vector data."""

        battery_state = self.robot.get_battery_state().result()
        version_state = self.robot.get_version_state().result()

        if battery_state:
            self.states.update(
                {
                    STATE_ROBOT_BATTERY_VOLTS: round(battery_state.battery_volts, 2),
                    STATE_ROBOT_BATTERY_LEVEL: BATTERYMAP_TO_STATE[
                        battery_state.battery_level
                    ],
                    STATE_ROBOT_IS_CHARGNING: battery_state.is_charging,
                    STATE_ROBOT_IS_ON_CHARGER: battery_state.is_on_charger_platform,
                    STATE_ROBOT_SUGGESTED_CHARGE: battery_state.suggested_charger_sec,
                }
            )

            if hasattr(battery_state, "cube_battery"):
                cube_battery = battery_state.cube_battery
                self.states.update(
                    {
                        STATE_CUBE_BATTERY_VOLTS: round(cube_battery.battery_volts, 2),
                        STATE_CUBE_BATTERY_LEVEL: BATTERYMAP_TO_STATE[
                            cube_battery.level
                        ]
                        or STATE_UNKNOWN,
                        STATE_CUBE_FACTORY_ID: cube_battery.factory_id,
                        STATE_CUBE_LAST_CONTACT: (
                            datetime.utcnow()
                            - timedelta(
                                seconds=int(cube_battery.time_since_last_reading_sec)
                            )
                        ).astimezone(pytz.UTC),
                    }
                )

        if version_state:
            self.states.update({STATE_FIRMWARE_VERSION: version_state.os_version})

        dispatcher_send(self.hass, UPDATE_SIGNAL)

        return True
