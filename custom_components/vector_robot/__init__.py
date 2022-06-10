"""Base definition of DDL Vector."""
from __future__ import annotations
from datetime import datetime, timedelta
from enum import IntEnum
from functools import partial

# Vector-A6S1
# 00908e7e
# 192.168.1.223

import logging
from typing import Optional
import anki_vector
import attr

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_NAME,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.loader import async_get_integration

from anki_vector import Robot

from .const import (
    CONF_IP,
    CONF_SERIAL,
    DOMAIN,
    PLATFORMS,
    STARTUP,
    UPDATE_BATTERY,
    UPDATE_SIGNAL,
)

from .helpers import (
    CubeBatteryInfo,
    CubeBatteryMap,
    RobotBatteryInfo,
    RobotBatteryMap,
)

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

    coordinator = VectorDataUpdateCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    await check_unique_id(hass, entry)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    # def shutdown(event: Event) -> None:
    #     robot: Robot = hass.data[DOMAIN][entry.entry_id]["robot"]
    #     robot.disconnect()

    # # Listen when EVENT_HOMEASSISTANT_STOP is fired
    # hass.data[DOMAIN][entry.entry_id]["listener"] = hass.bus.async_listen_once(
    #     EVENT_HOMEASSISTANT_STOP, shutdown
    # )

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
        self.name = f"{self._config_data[CONF_NAME]}_{self._config_data[CONF_SERIAL]}"
        self.robot_battery: RobotBatteryInfo = RobotBatteryInfo()
        self.cube_battery: CubeBatteryInfo = CubeBatteryInfo()
        self.robot_state = None
        self.is_added = False

        super().__init__(hass, _LOGGER, name=self.name, update_interval=SCAN_INTERVAL)

    def event_robot_state(self, robot, event_type, event):
        """Handle robot_state events."""
        _LOGGER.debug(robot)
        _LOGGER.debug(event_type)
        _LOGGER.debug(event)

    async def _async_update_data(self) -> datetime | None:
        """Update Vector data."""
        # if not self._is_added:
        #     _LOGGER.debug("Device not ready yet.")
        #     return False

        with anki_vector.AsyncRobot(
            self.serial,
            behavior_control_level=None,
            cache_animation_lists=False,
            default_logging=False,
        ) as robot:
            battery_state = robot.get_battery_state().result()
            version_state = robot.get_version_state().result()
            cube_battery = None
            # robot.conn.request_control()
            # cube_battery = robot.world.connect_cube().result()
            # robot.conn.release_control()

            if battery_state or cube_battery:
                if battery_state:
                    self.robot_battery.update(
                        battery_state.battery_volts,
                        RobotBatteryMap(battery_state.battery_level),
                        battery_state.is_charging,
                        battery_state.is_on_charger_platform,
                        battery_state.suggested_charger_sec,
                    )

                if cube_battery:
                    self.cube_battery.update(
                        cube_battery.battery_volts,
                        CubeBatteryMap(cube_battery.battery_level),
                        cube_battery.time_since_last_reading_sec,
                        cube_battery.factory_id,
                    )
                dispatcher_send(self.hass, UPDATE_BATTERY)

            if version_state:
                self.firmware_version = version_state.os_version

        # dispatcher_send(self.hass, UPDATE_SIGNAL)

        return True
