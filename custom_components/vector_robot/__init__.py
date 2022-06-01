"""Base definition of DDL Vector."""
from __future__ import annotations

# Vector-A6S1
# 00908e7e
# 192.168.1.223

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_NAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import (
    ATTR_MESSAGE,
    CONF_IP,
    CONF_SERIAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_GOTO_CHARGER,
    SERVICE_LEAVE_CHARGER,
    SERVICE_SPEAK,
    STARTUP,
)
from .pyHomeAssistantVector import Robot

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up cloud API connector from a config entry."""
    _LOGGER.debug("Entry data: %s", entry.data)
    _LOGGER.debug("Entry options: %s", entry.options)
    _LOGGER.debug("Entry unique ID: %s", entry.unique_id)

    hass.data.setdefault(DOMAIN, {})

    await check_unique_id(hass, entry)
    result = await _setup(hass, entry)

    # hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return result


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        for unsub in hass.data[DOMAIN][entry.entry_id]["api"].listeners:
            unsub()
        hass.data[DOMAIN].pop(entry.entry_id)

        return True

    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup the integration using a config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP, integration.version)

    hass.data[DOMAIN][entry.entry_id] = {"robot": Robot(entry.data.get(CONF_SERIAL))}

    api = VectorAPI(hass, entry)
    hass.data[DOMAIN][entry.entry_id]["api"] = api

    hass.services.async_register(
        DOMAIN, SERVICE_GOTO_CHARGER, api.async_drive_on_charger
    )
    hass.services.async_register(
        DOMAIN, SERVICE_LEAVE_CHARGER, api.async_drive_off_charger
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SPEAK,
        api.async_drive_off_charger,
        schema={vol.Required(ATTR_MESSAGE): str},
    )

    return True


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


class VectorAPI:
    """Defines a Vector API connector."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the connection."""
        self.hass = hass
        self._config_data = entry.data
        self.robot: Robot = hass.data[DOMAIN][entry.entry_id]["robot"]

    async def async_connect(self) -> None:
        """Connect to Vector."""
        self.robot.connect()
        await self.hass.async_add_executor_job(self.robot.conn.request_control)

    async def async_disconnect(self) -> None:
        """Disconnect from Vector."""
        await self.hass.async_add_executor_job(self.robot.conn.release_control)
        self.robot.disconnect()

    async def async_drive_on_charger(self) -> None:
        """Send Vector to the charger."""
        await self.async_connect()
        await self.hass.async_add_executor_job(self.robot.behavior.drive_on_charger)
        await self.async_disconnect()

    async def async_drive_off_charger(self) -> None:
        """Send Vector to the charger."""
        await self.async_connect()
        await self.hass.async_add_executor_job(self.robot.behavior.drive_off_charger)
        await self.async_disconnect()

    async def async_tts(self, message: str) -> None:
        """Make Vector speak."""
        await self.async_connect()
        await self.hass.async_add_executor_job(self.robot.behavior.say_text, message)
        await self.async_disconnect()
