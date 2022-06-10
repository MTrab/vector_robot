"""Vector robot buttons."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass

import logging

from homeassistant.backports.enum import StrEnum
from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VectorDataUpdateCoordinator

from .const import DOMAIN, SERVICE_GOTO_CHARGER

from .base import VectorBase

_LOGGER = logging.getLogger(__name__)


class VectorButtonTypes(StrEnum):
    """Vector button types."""

    LEAVE_CHARGER = SERVICE_GOTO_CHARGER


@dataclass
class VectorButtonEntityDescription(ButtonEntityDescription):
    """Describes a Vector button."""

    call_function: str | None = None


BUTTONS = [
    VectorButtonEntityDescription(
        key=VectorButtonTypes.LEAVE_CHARGER,
        name="Go to charger",
        icon=None,
        call_function="async_drive_on_charger",
    ),
]


class VectorButton(VectorBase, ButtonEntity):
    """Defines a base Vector button."""

    entity_description: VectorButtonEntityDescription

    def __init__(self, coordinator: VectorDataUpdateCoordinator, call_function: str):
        super().__init__(coordinator)
        self._call_function = call_function

    async def async_press(self) -> None:
        """Handles button press."""
        await getattr(self, self._call_function)


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create Vector buttons."""
    coordinator = hass.data[DOMAIN][config.entry_id]["coordinator"]

    entities = []
    for button in BUTTONS:
        if button.key == VectorButtonTypes.LEAVE_CHARGER:
            entities.append(VectorButton(coordinator, button.call_function))

    async_add_entities(entities, True)
