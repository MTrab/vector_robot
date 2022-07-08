"""Base definition of DDL Vector."""
# pylint: disable=unused-argument,protected-access
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from enum import IntEnum
from functools import partial
from typing import Optional, cast

import pytz
from ha_vector.events import Events
from ha_vector.exceptions import (
    VectorConnectionException,
    VectorNotFoundException,
    VectorTimeoutException,
    VectorUnauthenticatedException,
)
from ha_vector.robot import AsyncRobot
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_NAME, CONF_PASSWORD, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.loader import async_get_integration

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
    STATE_HEAD_TRACKING_ID,
    STATE_ROBOT_BATTERY_LEVEL,
    STATE_ROBOT_BATTERY_VOLTS,
    STATE_ROBOT_IS_CHARGNING,
    STATE_ROBOT_IS_ON_CHARGER,
    STATE_ROBOT_SUGGESTED_CHARGE,
    STATE_STIMULATION,
    STATE_TIME_STAMPED,
    UPDATE_SIGNAL,
)
from .helpers.storage import VectorStore
from .schemes import TTS
from .states import FEATURES_TO_IGNORE, STIMULATIONS_TO_IGNORE, VectorStates
from .vector_utils import DataRunner
from .vector_utils.config import validate_input
from .vector_utils.observations import Face, Observation
from .vector_utils.speech import VectorSpeachType, VectorSpeech

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
    _LOGGER.debug("Vector config: %s", config)

    dataset = DataRunner(hass, store.path)
    await dataset.async_refresh()

    try:
        coordinator = VectorDataUpdateCoordinator(hass, entry, config, dataset.path)
    except VectorUnauthenticatedException:
        await validate_input(hass, entry.data)
        try:
            store = VectorStore(hass, entry.data[CONF_NAME])
            config = cast(Optional[dict], await store.async_load())
            _LOGGER.debug("Retrying with Vector config: %s", config)
            coordinator = VectorDataUpdateCoordinator(hass, entry, config, dataset.path)
        except VectorUnauthenticatedException as exc:
            raise HomeAssistantError from exc
    except (VectorNotFoundException, VectorTimeoutException, VectorConnectionException):
        _LOGGER.error("Couldn't connect to %s", entry.data[CONF_NAME])
        # async_call_later(hass,timedelta(seconds=10),async_setup_entry(hass,entry))
        # hass.loop.call_later(10, async_setup_entry,hass,entry)
        return False
    except Exception as exc:
        raise HomeAssistantError from exc

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

        self.robot = AsyncRobot(
            self.serial,
            behavior_control_level=None,
            cache_animation_lists=False,
            enable_face_detection=True,
            estimate_facial_expression=True,
            enable_audio_feed=False,
            enable_nav_map_feed=True,
            name=self._config_data[CONF_NAME],
            ip_address=self._config_data[CONF_IP],
            config=self._config,
            force_async=True,
        )

        self.states = VectorStates()
        super().__init__(hass, _LOGGER, name=self.name, update_interval=SCAN_INTERVAL)

        self.robot.connect()

        self.speak = VectorSpeech(self.robot, self._dataset)
        self.observations = Observation()

        async def on_robot_observed_face(robot, event_type, event, done=None):
            for face in robot.world.visible_faces:
                if not face.name == "":
                    _LOGGER.debug(face)
                    # face = Face(event.face_id, event.name, datetime.now().timestamp)
                    self.observations.faces.update(
                        {
                            face.name: {
                                "id": face.face_id,
                                "expression": face.expression,
                                "expression_score": None,  # face.expression_score,
                                "last_seen": datetime.now(),
                            }
                        }
                    )
                    dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_observations")

        async def on_robot_time_stamped_status(robot, event_type, event, done=None):
            """Handle time stamped events."""
            if event.status.feature_status.feature_name:
                if not event.status.feature_status.feature_name in FEATURES_TO_IGNORE:
                    _LOGGER.debug(
                        "Setting time stamped event: %s",
                        event,
                    )

                    feature = event.status.feature_status.feature_name
                    self.states.update({STATE_TIME_STAMPED: str(feature).lower()})

                    dispatcher_send(self.hass, UPDATE_SIGNAL)

        async def on_robot_stimulation(robot, event_type, event, done=None):
            """Handle robot_state events."""
            # emotion_events: "PettingStarted"
            # emotion_events: "PettingBlissLevelIncrease"
            # emotion_events: "ReactToSoundAwake"
            if not event.emotion_events:
                return
            myevent = event.emotion_events[0]
            _LOGGER.debug(event)
            _LOGGER.debug(myevent)
            if not myevent in STIMULATIONS_TO_IGNORE:
                self.states.update({STATE_STIMULATION: str(myevent[0]).lower()})
                dispatcher_send(self.hass, UPDATE_SIGNAL)

            if myevent == "ReactToTriggerWord":
                await self.speak.async_speak(text="You called?")
            elif myevent == "NoValidVoiceIntent":
                await self.speak.async_speak(text="Sorry, I didn't understand.")
            elif myevent in ["PettingStarted", "PettingBlissLevelIncrease"]:
                await self.speak.async_speak(predefined=VectorSpeachType.PETTING)

        # async def on_event(robot, event_type, event, done=None):
        #     """Generic debug event callback."""
        #     _LOGGER.info("Integration got an event call.")
        #     _LOGGER.debug(
        #         "\nEvent data:\nRobot: %s\nEvent_type: %s\nEvent: %s",
        #         robot,
        #         event_type,
        #         event,
        #     )

        async def on_robot_state(robot, event_type, event, done=None):
            """Update robot states."""
            self.states.update(
                {
                    STATE_CARRYING_OBJECT: event.carrying_object_id,
                    STATE_CARRYING_OBJECT_ON_TOP: event.carrying_object_on_top_id,
                    STATE_HEAD_TRACKING_ID: event.head_tracking_object_id,
                }
            )

        # Event: pose {
        #   x: -81.23602294921875
        #   y: -114.03437805175781
        #   z: 2.5920803546905518
        #   q0: 0.9856083989143372
        #   q3: 0.16904449462890625
        #   origin_id: 7
        # }
        # pose_angle_rad: 0.3397202789783478
        # pose_pitch_rad: -0.11033941805362701
        # head_angle_rad: -0.36896002292633057
        # lift_height_mm: 32.0
        # accel {
        #   x: -4641.689453125
        #   y: 185.6196746826172
        #   z: 8891.78125
        # }
        # gyro {
        #   x: 0.00019037630409002304
        #   y: -0.0008325017988681793
        #   z: 5.6976965424837545e-05
        # }
        # carrying_object_id: -1
        # carrying_object_on_top_id: -1
        # head_tracking_object_id: -1
        # last_image_time_stamp: 51894009
        # status: 1056512
        # prox_data {
        #   distance_mm: 248
        #   signal_quality: 0.010212385095655918
        # }
        # touch_data {
        #   raw_touch_value: 4634
        # }

        ### Subscribe to events
        self.robot.events.subscribe(on_robot_state, Events.robot_state)
        # self.robot.events.subscribe(on_lost_cube_connection, Events.cube_connection_lost)
        # self.robot.events.subscribe(on_object_appeared, Events.object_appeared)
        # self.robot.events.subscribe(on_object_disappeared, Events.object_disappeared)
        # self.robot.events.subscribe(on_robot_observed_object, Events.robot_observed_object)
        # self.robot.events.subscribe(on_user_intent, Events.user_intent)
        self.robot.events.subscribe(
            on_robot_observed_face, Events.robot_changed_observed_face_id
        )
        self.robot.events.subscribe(on_robot_observed_face, Events.robot_observed_face)
        self.robot.events.subscribe(
            on_robot_time_stamped_status, Events.time_stamped_status
        )
        self.robot.events.subscribe(on_robot_stimulation, Events.stimulation_info)

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

        def load_anim_list() -> None:
            try:
                self.robot.anim.load_animation_list()
            except VectorTimeoutException:
                _LOGGER.debug(
                    "Couldn't load animations list, got a timeout - trying again in 5 seconds."
                )
                async_call_later(hass, timedelta(seconds=5), load_anim_list)

        self.robot.vision.enable_face_detection(
            detect_faces=True, estimate_expression=True
        )
        load_anim_list()

    async def async_speak_joke(self, *args, **kwargs) -> None:
        """Tell a joke."""
        await self.speak.async_speak(
            predefined=VectorSpeachType.JOKE, force_speech=True
        )

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
        await self.speak.async_speak(
            text=service_call.data[ATTR_MESSAGE],
            use_vector_voice=service_call.data[ATTR_USE_VECTOR_VOICE],
            force_speech=True,
        )

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

            dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_battery")

        if version_state:
            self.states.update({STATE_FIRMWARE_VERSION: version_state.os_version})

            dispatcher_send(self.hass, UPDATE_SIGNAL)

        return True
