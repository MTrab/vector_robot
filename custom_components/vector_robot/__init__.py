"""Base definition of DDL Vector."""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import IntEnum
from functools import partial

# Vector-A6S1
# 00908e7e
# 192.168.1.223

import logging
import random
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_NAME,
    CONF_PASSWORD,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.loader import async_get_integration
import pytz

from ha_vector.robot import Robot
from ha_vector.events import Events
from ha_vector.exceptions import VectorConnectionException
from ha_vector.user_intent import UserIntent, UserIntentEvent


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
    STATE_CARRYING_OBJECT,
    STATE_CARRYING_OBJECT_ON_TOP,
    STATE_CUBE_BATTERY_LEVEL,
    STATE_CUBE_BATTERY_VOLTS,
    STATE_CUBE_FACTORY_ID,
    STATE_CUBE_LAST_CONTACT,
    STATE_FIRMWARE_VERSION,
    STATE_FOUND_OBJECT,
    STATE_HEAD_TRACKING_ID,
    STATE_LIFT_IN_FOV,
    STATE_ROBOT_BATTERY_LEVEL,
    STATE_ROBOT_BATTERY_VOLTS,
    STATE_ROBOT_IS_CHARGNING,
    STATE_ROBOT_IS_ON_CHARGER,
    STATE_ROBOT_SUGGESTED_CHARGE,
    STATE_STIMULATION,
    STATE_TIME_STAMPED,
    UPDATE_SIGNAL,
)

from .states import (
    FEATURES_TO_IGNORE,
    STIMULATIONS_TO_IGNORE,
    VectorStates,
)
from .schemes import TTS
from .vector_utils import Chatter, DataRunner
from .vector_utils.const import VectorDatasets

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

    dataset = DataRunner(hass)
    await dataset.async_refresh()

    coordinator = VectorDataUpdateCoordinator(hass, entry)
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

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
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
        self.robot = Robot(
            self.serial,
            behavior_control_level=None,
            default_logging=False,
            cache_animation_lists=False,
            enable_face_detection=True,
            estimate_facial_expression=True,
            enable_audio_feed=True,
            # name=self._config_data[CONF_NAME],
            ip=self._config_data[CONF_IP],
        )
        self.states = VectorStates()
        self.chatter = Chatter()
        self.chatter.get_text(VectorDatasets.DIALOGS, "cliff")

        self.robot.connect()

        def on_robot_user_intent(robot, event_type, event):
            """React to user intents."""
            _LOGGER.debug(event)
            user_intent = UserIntent(event)
            _LOGGER.debug("Received %s", user_intent.intent_event)
            _LOGGER.debug(user_intent.intent_data)
            if user_intent.intent_event is UserIntentEvent.greeting_hello:
                Str = random.randint(1, 3)
                if not robot.conn._has_control:
                    robot.conn.request_control()

                if Str == 1:
                    robot.behavior.say_text("Stop disturbing me. I'm busy")
                if Str == 2:
                    robot.behavior.say_text("You again. You're always here")
                if Str == 3:
                    robot.behavior.say_text("Can I please have 2 minutes peace?")
                robot.conn.release_control()

        def on_event(robot, event_type, event):
            """Used for testing events."""
            _LOGGER.info("Event type: %s\nEvent: %s", event_type, event)

        def on_robot_state(robot, event_type, event):
            """Extract data from robot state."""
            self.states.update(
                {
                    STATE_CARRYING_OBJECT: event.carrying_object_id
                    if event.carrying_object_id != -1
                    else None,
                    STATE_CARRYING_OBJECT_ON_TOP: event.carrying_object_on_top_id
                    if event.carrying_object_on_top_id != -1
                    else None,
                    STATE_HEAD_TRACKING_ID: event.head_tracking_object_id
                    if event.head_tracking_object_id != -1
                    else None,
                }
            )

            if hasattr(event.prox_data, "lift_in_fov"):
                self.states.update(
                    {
                        STATE_LIFT_IN_FOV: bool(event.prox_data.lift_in_fov),
                    }
                )
            else:
                self.states.update(
                    {
                        STATE_LIFT_IN_FOV: False,
                    }
                )

            if hasattr(event.prox_data, "found_object"):
                self.states.update(
                    {
                        STATE_FOUND_OBJECT: bool(event.prox_data.found_object),
                    }
                )
            else:
                self.states.update(
                    {
                        STATE_FOUND_OBJECT: False,
                    }
                )

        def on_robot_time_stamped_status(robot, event_type, event):
            """Handle time stamped events."""
            if event.status.feature_status.feature_name:
                if not event.status.feature_status.feature_name in FEATURES_TO_IGNORE:
                    feature = event.status.feature_status.feature_name
                    self.states.update({STATE_TIME_STAMPED: str(feature).lower()})

                    dispatcher_send(self.hass, UPDATE_SIGNAL)

        def on_robot_stimulation(robot, event_type, event):
            """Handle robot_state events."""
            # emotion_events: "PettingStarted"
            # emotion_events: "PettingBlissLevelIncrease"
            # emotion_events: "ReactToSoundAwake"

            if not event.emotion_events:
                return
            myevent = event.emotion_events
            if not myevent[0] in STIMULATIONS_TO_IGNORE:
                self.states.update({STATE_STIMULATION: str(myevent[0]).lower()})

            if myevent == ["PettingStarted"]:
                _LOGGER.debug("Petting started")
                # data = {ATTR_MESSAGE: "Oh so good!", ATTR_USE_VECTOR_VOICE: True}
                # self.hass.services.call(
                #     DOMAIN,
                #     SERVICE_SPEAK,
                #     ServiceCall(
                #         DOMAIN,
                #         SERVICE_SPEAK,
                #         data=data,
                #     ),
                # )
                if not robot.conn._has_control:
                    robot.conn.request_control()
                robot.behavior.say_text(
                    text="Oh so good!",
                )
                robot.conn.release_control(timeout=1.0)
            # elif myevent == ["PettingBlissLevelIncrease"]:
            #     _LOGGER.debug("Still being petted")
            #     self.robot.conn.request_control()
            #     self.robot.behavior.say_text(
            #         text="Oh yes - right there!",
            #     )
            #     self.robot.conn.release_control(timeout=1.0)

            dispatcher_send(self.hass, UPDATE_SIGNAL)

        def on_robot_wake_word(robot, event_type, event):
            """React to wake word."""

            if event == "wake_word_begin":
                robot.conn.request_control()
                robot.behavior.say_text(
                    text="You called!",
                )
                robot.conn.release_control()

        ### Subscribe to events
        # Handle user intents
        self.robot.events.subscribe(on_robot_user_intent, Events.user_intent)
        # Handle stimulations
        self.robot.events.subscribe(on_robot_stimulation, Events.stimulation_info)
        # Handle wake words
        self.robot.events.subscribe(on_robot_wake_word, Events.wake_word)
        # Handle time stamped events
        self.robot.events.subscribe(
            on_robot_time_stamped_status, Events.time_stamped_status
        )
        # Extract information from robot state events
        self.robot.events.subscribe(on_robot_state, Events.robot_state)

        # self.robot.events.subscribe(self.on_event, Events.robot_observed_object)
        # self.robot.events.subscribe(self.on_event, Events.robot_observed_face)

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

    async def async_drive_on_charger(self, _) -> None:
        """Send Vector to the charger."""
        _LOGGER.debug("Asking Vector to go onto the charger")
        self.robot.conn.request_control()
        self.robot.behavior.drive_on_charger()
        self.robot.conn.release_control(timeout=1.0)

    async def async_drive_off_charger(self, _) -> None:
        """Send Vector to the charger."""
        _LOGGER.debug("Asking Vector to leave the charger")
        self.robot.conn.request_control()
        self.robot.behavior.drive_off_charger()
        self.robot.conn.release_control(timeout=1.0)

    async def async_tts(self, service_call: ServiceCall) -> None:
        """Make Vector speak."""
        _LOGGER.debug("Asking Vector to say a text")
        try:
            self.robot.conn.request_control()
            self.robot.behavior.say_text(
                text=service_call.data[ATTR_MESSAGE],
                use_vector_voice=service_call.data[ATTR_USE_VECTOR_VOICE],
            )
            self.robot.conn.release_control(timeout=1.0)
        except VectorConnectionException:
            _LOGGER.warning("Something happend while sending TTS to Vector :(")

    async def _async_update_data(self) -> datetime | None:
        """Update Vector data."""

        battery_state = await self.hass.async_add_executor_job(
            self.robot.get_battery_state
        )
        version_state = await self.hass.async_add_executor_job(
            self.robot.get_version_state
        )

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
