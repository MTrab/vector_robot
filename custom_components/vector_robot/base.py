"""Base definitions."""
from __future__ import annotations
from datetime import timedelta
from functools import partial

import logging
from typing import Any
import anki_vector

from homeassistant.core import ServiceCall
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from anki_vector.events import Events
from anki_vector.exceptions import VectorTimeoutException, VectorAsyncException

from . import VectorDataUpdateCoordinator, VectorConnectionState

from .const import ATTR_MESSAGE, DOMAIN, ATTR_USE_VECTOR_VOICE

_LOGGER = logging.getLogger(__name__)


def connect(self) -> bool:
    """Open robot connection."""
    _LOGGER.debug("Connecting to Vector")
    try:
        self.connection_state = VectorConnectionState.CONNECTING
        self.robot.connect()
        self.connection_state = VectorConnectionState.CONNECTED

        # Event subscriptions
        # on_robot_state = partial(self.api.event_robot_state, self.robot)
        # self.robot.events.subscribe(on_robot_state, Events.robot_state)

        return True
    except VectorAsyncException:
        _LOGGER.debug("Async exception, returning true anyway")
        self.connection_state = VectorConnectionState.CONNECTED
        return True
    except VectorTimeoutException:
        _LOGGER.warning("Timeout connecting to Vector, trying again later.")
        self.connection_state = VectorConnectionState.DISCONNECTED
        async_call_later(self.hass, timedelta(minutes=1), partial(self.connect))
        return False


class VectorBase(CoordinatorEntity):
    """Defines a Vector base class."""

    _attr_icon = "mdi:robot"

    def __init__(self, coordinator: VectorDataUpdateCoordinator):
        """Initialise a Vector base."""
        super().__init__(coordinator)
        self.api: VectorDataUpdateCoordinator = coordinator

    @property
    def device_info(self):
        """Set device information."""

        return {
            "identifiers": {(DOMAIN, self.api.entry_id, self.api.friendly_name)},
            "name": str(self.api.friendly_name),
            "manufacturer": "Digital Dream Labs / Anki",
            "model": "Vector",
            "sw_version": self.api.firmware_version,
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.api.is_added = True

    async def async_drive_on_charger(
        self, entity: Entity, service_call: ServiceCall
    ) -> None:
        """Send Vector to the charger."""
        with anki_vector.Robot(
            self.api.serial,
            cache_animation_lists=False,
            default_logging=False,
        ) as robot:
            robot.behavior.drive_on_charger

    async def async_drive_off_charger(
        self, entity: Entity, service_call: ServiceCall
    ) -> None:
        """Send Vector to the charger."""
        with anki_vector.Robot(
            self.api.serial,
            cache_animation_lists=False,
            default_logging=False,
        ) as robot:
            robot.behavior.drive_off_charger

    async def async_tts(self, entity: Entity, service_call: ServiceCall) -> None:
        """Make Vector speak."""
        with anki_vector.Robot(
            self.api.serial,
            cache_animation_lists=False,
            default_logging=False,
        ) as robot:
            robot.behavior.say_text(
                text=service_call.data[ATTR_MESSAGE],
                use_vector_voice=service_call.data[ATTR_USE_VECTOR_VOICE],
            )
