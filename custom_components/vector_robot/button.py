"""Vector robot buttons."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.backports.enum import StrEnum
from homeassistant.components.button import (
    ENTITY_ID_FORMAT,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VectorDataUpdateCoordinator
from .base import VectorBase, VectorBaseEntityDescription
from .const import BUTTON_GENERIC, DOMAIN, SERVICE_GOTO_CHARGER, SERVICE_LEAVE_CHARGER

_LOGGER = logging.getLogger(__name__)


class VectorButtonTypes(StrEnum):
    """Vector button types."""

    LEAVE_CHARGER = SERVICE_LEAVE_CHARGER
    GOTO_CHARGER = SERVICE_GOTO_CHARGER
    GENERIC = BUTTON_GENERIC


@dataclass
class VectorButtonEntityDescription(
    VectorBaseEntityDescription, ButtonEntityDescription
):
    """Describes a Vector button."""

    call_function: str | None = None
    call_param: dict | None = None


BUTTONS = [
    VectorButtonEntityDescription(
        key=VectorButtonTypes.LEAVE_CHARGER,
        name="Leave the charger",
        icon="mdi:home-export-outline",
        call_function="async_drive_off_charger",
    ),
    VectorButtonEntityDescription(
        key=VectorButtonTypes.GOTO_CHARGER,
        name="Go to the charger",
        icon="mdi:home-lightning-bolt",
        call_function="async_drive_on_charger",
    ),
    VectorButtonEntityDescription(
        key=VectorButtonTypes.GENERIC,
        name="Tell me a joke",
        icon="mdi:account-voice",
        call_function="async_speak_joke",
    ),
]


class VectorButton(VectorBase, ButtonEntity):
    """Defines a base Vector button."""

    entity_description: VectorButtonEntityDescription

    def __init__(
        self,
        coordinator: VectorDataUpdateCoordinator,
        description: VectorButtonEntityDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._call_function = description.call_function
        self.entity_id = ENTITY_ID_FORMAT.format(
            f"{coordinator.name} {description.key}"
        )
        self._attr_unique_id = f"{coordinator.name}_button_{description.key}"
        self._attr_icon = description.icon
        self._coordinator = coordinator

    async def async_press(self) -> None:
        """Handles button press."""
        call = getattr(self._coordinator, self._call_function)
        await call()


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create Vector buttons."""
    coordinator = hass.data[DOMAIN][config.entry_id]["coordinator"]

    entities = []
    for button in BUTTONS:
        entities.append(VectorButton(coordinator, button))

    async_add_entities(entities, True)
