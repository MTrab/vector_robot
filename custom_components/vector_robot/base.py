"""Base definitions."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import timedelta
from functools import partial

import logging

from homeassistant.helpers.entity import EntityDescription
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ha_vector.exceptions import VectorTimeoutException, VectorAsyncException

from . import VectorDataUpdateCoordinator, VectorConnectionState

from .const import DOMAIN, STATE_FIRMWARE_VERSION, STATE_NO_DATA

_LOGGER = logging.getLogger(__name__)


def connect(self) -> bool:
    """Open robot connection."""
    _LOGGER.debug("Connecting to Vector")
    try:
        self.connection_state = VectorConnectionState.CONNECTING
        self.robot.connect()
        self.connection_state = VectorConnectionState.CONNECTED

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


@dataclass
class VectorBaseEntityDescription(EntityDescription):
    """Describes a Vector sensor."""

    state_attr: str | None = None
    vector_attributes: dict | None = field(default_factory=dict)
    translate_key: str | None = None
    start_value: str = STATE_NO_DATA


class VectorBase(CoordinatorEntity):
    """Defines a Vector base class."""

    _attr_icon = "mdi:robot"

    def __init__(self, coordinator: VectorDataUpdateCoordinator):
        """Initialise a Vector base."""
        super().__init__(coordinator)
        self.api: VectorDataUpdateCoordinator = coordinator
        self._generation = "1.0" if self.api.serial.startswith("00") else "2.0"
        self._vendor = "Anki" if self._generation == "1.0" else "Digital Dream Labs"

    @property
    def device_info(self):
        """Set device information."""

        return {
            "identifiers": {(DOMAIN, self.api.entry_id, self.api.friendly_name)},
            "name": str(self.api.friendly_name),
            "manufacturer": self._vendor,
            "model": "Vector",
            "sw_version": self.api.states[STATE_FIRMWARE_VERSION]
            if STATE_FIRMWARE_VERSION in self.api.states
            else STATE_UNKNOWN,
            "hw_version": self._generation,
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.api.is_added = True
