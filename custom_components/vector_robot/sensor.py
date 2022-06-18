"""Vector robot sensors."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    ENTITY_ID_FORMAT,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .base import VectorBase
from .const import (
    DOMAIN,
    ICON_CUBE,
    ICON_ROBOT,
    LANG_BATTERY,
    LANG_STATE,
    LANG_STIMULI,
    STATE_CUBE_BATTERY_LEVEL,
    STATE_CUBE_BATTERY_VOLTS,
    STATE_CUBE_FACTORY_ID,
    STATE_CUBE_LAST_CONTACT,
    STATE_FIRMWARE_VERSION,
    STATE_ROBOT_BATTERY_LEVEL,
    STATE_ROBOT_BATTERY_VOLTS,
    STATE_ROBOT_IS_CHARGNING,
    STATE_ROBOT_IS_ON_CHARGER,
    STATE_STIMULATION,
    STATE_TIME_STAMPED,
    UPDATE_SIGNAL,
    VECTOR_ICON,
)

_LOGGER = logging.getLogger(__name__)


class VectorSensorType(IntEnum):
    """Vector sensor types."""

    BATTERY = 0
    STATE = 1


class VectorSensorFeature(IntEnum):
    """Different battery sensor types."""

    BATTERY_ROBOT = 0
    BATTERY_CUBE = 1
    STATUS = 2


@dataclass
class VectorSensorEntityDescription(SensorEntityDescription):
    """Describes a Vector sensor."""

    state_attr: str | None = None
    sensor_type: VectorSensorType = VectorSensorType.STATE
    vector_attributes: dict | None = field(default_factory=dict)
    translate_key: str | None = None


SENSORS = [
    VectorSensorEntityDescription(
        key=VectorSensorFeature.BATTERY_ROBOT,
        name="Battery Level",
        device_class=SensorDeviceClass.BATTERY,
        icon=VECTOR_ICON[ICON_ROBOT],
        state_attr=STATE_ROBOT_BATTERY_LEVEL,
        sensor_type=VectorSensorType.BATTERY,
        translate_key=LANG_BATTERY,
        vector_attributes={
            STATE_ROBOT_BATTERY_VOLTS: "voltage",
            STATE_ROBOT_IS_CHARGNING: "charging",
            STATE_ROBOT_IS_ON_CHARGER: "on_charger",
        },
    ),
    VectorSensorEntityDescription(
        key=VectorSensorFeature.BATTERY_CUBE,
        name="Cube battery Level",
        device_class=SensorDeviceClass.BATTERY,
        icon=VECTOR_ICON[ICON_CUBE],
        state_attr=STATE_CUBE_BATTERY_LEVEL,
        sensor_type=VectorSensorType.BATTERY,
        translate_key=LANG_BATTERY,
        vector_attributes={
            STATE_CUBE_BATTERY_VOLTS: "voltage",
            STATE_CUBE_FACTORY_ID: "mac_address",
            STATE_CUBE_LAST_CONTACT: "last_contact",
        },
    ),
    VectorSensorEntityDescription(
        key=VectorSensorFeature.STATUS,
        name="Status",
        icon=VECTOR_ICON[ICON_ROBOT],
        state_attr=STATE_TIME_STAMPED,
        sensor_type=VectorSensorType.STATE,
        translate_key=LANG_STATE,
        vector_attributes={
            STATE_FIRMWARE_VERSION: "firmware_version",
        },
    ),
    VectorSensorEntityDescription(
        key=VectorSensorFeature.STATUS,
        name="Stimulation",
        icon=VECTOR_ICON[ICON_ROBOT],
        state_attr=STATE_STIMULATION,
        sensor_type=VectorSensorType.STATE,
        translate_key=LANG_STIMULI,
    ),
]


class VectorBaseSensorEntity(VectorBase, SensorEntity):
    """Defines a Vector sensor."""

    entity_description: VectorSensorEntityDescription

    def __init__(self, coordinator, description: VectorSensorEntityDescription):
        """Initialize a base sensor."""
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.entity_description = description

        self._attr_unique_id = f"{self.coordinator.name}_{self.entity_description.name}"
        self.entity_id = ENTITY_ID_FORMAT.format(
            f"{coordinator.name} {description.name}"
        )
        self._attr_icon = description.icon

        self._attr_extra_state_attributes = {}
        self._attr_native_value = STATE_UNKNOWN
        self._attr_device_class = f"{DOMAIN}__{self.entity_description.translate_key}"
        self._attr_name = self.entity_description.name

    async def async_added_to_hass(self) -> None:
        """Actions when added to Home Assistant."""
        await super().async_added_to_hass()

        # Listen for battery updates
        async_dispatcher_connect(self.hass, UPDATE_SIGNAL, self.async_update_entity)

    async def async_update_entity(self) -> None:
        """Update the entity."""
        # _LOGGER.debug(
        #     "Update called for %s\nWe have these states available:\n%s",
        #     self._attr_name,
        #     self.coordinator.states,
        # )
        self._attr_native_value = (
            self.coordinator.states[self.entity_description.state_attr]
            if self.entity_description.state_attr in self.coordinator.states
            else STATE_UNKNOWN
        )

        if hasattr(self.entity_description, "vector_attributes"):
            states = self.coordinator.states

            attributes = {}
            for prop, attr in self.entity_description.vector_attributes.items():
                if prop in states:
                    prop_data = states[prop]
                    if not isinstance(prop_data, type(None)):
                        attributes[attr] = prop_data

            self._attr_extra_state_attributes.update(attributes)

        self.async_write_ha_state()


class VectorStateSensorEntity(VectorBaseSensorEntity):
    """Defines a Vector state sensor."""


class VectorBatterySensorEntity(VectorBaseSensorEntity):
    """Defines a Vector battery sensor."""


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,  # pylint: disable=unused-argument
    discovery_info: DiscoveryInfoType | None = None,  # pylint: disable=unused-argument
) -> None:
    """Set up a Vector sensor."""

    @callback
    def schedule_import(_):
        """Schedule delayed import after HA is fully started."""
        async_call_later(hass, 10, do_import)

    @callback
    def do_import(_):
        """Process YAML import."""
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(config)
            )
        )

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, schedule_import)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Vector sensor entries."""
    coordinator = hass.data[DOMAIN][config.entry_id]["coordinator"]

    entities = []
    for sensor in SENSORS:
        if sensor.sensor_type == VectorSensorType.BATTERY:
            constructor = VectorBatterySensorEntity(coordinator, sensor)
        elif sensor.sensor_type == VectorSensorType.STATE:
            constructor = VectorStateSensorEntity(coordinator, sensor)

        entities.append(constructor)

    async_add_entities(entities, True)
