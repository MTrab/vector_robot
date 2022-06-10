"""Vector robot sensors."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from functools import partial

import logging
from typing import Any, Mapping

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .base import VectorBase
from .const import (
    DOMAIN,
    SERVICE_GOTO_CHARGER,
    SERVICE_LEAVE_CHARGER,
    SERVICE_SPEAK,
    UPDATE_BATTERY,
)
from .helpers import CubeBatteryMap, RobotBatteryMap, CubeBatteryInfo, RobotBatteryInfo
from .schemes import TTS

_LOGGER = logging.getLogger(__name__)


@dataclass
class VectorSensorEntityDescription(SensorEntityDescription):
    """Describes a Vector sensor."""


class VectorBatterySensorFeature(IntEnum):
    """Different battery sensor types."""

    ROBOT = 0
    CUBE = 1


class VectorBaseSensorEntity(VectorBase):
    """Defines a Vector sensor."""

    entity_description: VectorSensorEntityDescription

    def __init__(self, coordinator):
        """Initialize a base sensor."""
        super().__init__(coordinator)

        platform = entity_platform.async_get_current_platform()
        platform.async_register_entity_service(
            SERVICE_SPEAK,
            TTS,
            partial(self.async_tts),
        )
        platform.async_register_entity_service(
            SERVICE_LEAVE_CHARGER, {}, self.async_drive_off_charger
        )

    # async def async_process_data(self) -> None:
    #     """Process data from API."""


class VectorBatterySensorEntity(VectorBaseSensorEntity, SensorEntity):
    """Defines a Vector battery sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY

    def __init__(
        self,
        coordinator,
        feature: VectorBatterySensorFeature = VectorBatterySensorFeature.ROBOT,
    ):
        """Init the sensor."""
        super().__init__(coordinator)
        self.feature = feature
        self.coordinator = coordinator

        self._attributes = {}
        self._state = None

        if self.feature == VectorBatterySensorFeature.CUBE:
            # Cube battery sensor
            self._attr_name = f"{self.coordinator.name} Cube Battery Level"
            self._attr_unique_id = f"{self.coordinator.name}_cube_batterylevel"
            self._attr_icon = "mdi:cube"
        elif self.feature == VectorBatterySensorFeature.ROBOT:
            # Robot battery sensor
            self._attr_name = f"{self.coordinator.name} Battery Level"
            self._attr_unique_id = f"{self.coordinator.name}_batterylevel"

    async def async_update_battery(self):
        """Updates battery state when received."""

        if self.feature == VectorBatterySensorFeature.CUBE:
            battery: CubeBatteryInfo = self.coordinator.cube_battery
            self._state = battery.level
            self._attributes = {
                "voltage": round(battery.voltage, 2),
                "last_reading": battery.last_reading,
                "factory_id": battery.factory_id,
            }

        if self.feature == VectorBatterySensorFeature.ROBOT:
            battery: RobotBatteryInfo = self.coordinator.robot_battery
            self._state = battery.level
            self._attributes = {
                "voltage": round(battery.voltage, 2),
                "charging": battery.is_charging,
                "on_charger": battery.on_charger,
            }

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Connect to dispatchers when HASS is loaded."""
        await super().async_added_to_hass()

        if self.feature == VectorBatterySensorFeature.CUBE:
            # Cube battery sensor
            battery: CubeBatteryInfo = self.coordinator.cube_battery
        elif self.feature == VectorBatterySensorFeature.ROBOT:
            # Robot battery sensor
            battery: RobotBatteryInfo = self.coordinator.robot_battery
            self._state = battery.level
            if isinstance(battery.voltage, type(None)):
                self._attributes = {
                    "level": None,
                    "voltage": None,
                    "charging": None,
                    "on_charger": None,
                }
            else:
                self._attributes = {
                    "level": battery.level,
                    "voltage": round(float(battery.voltage), 2),
                    "charging": battery.is_charging,
                    "on_charger": battery.on_charger,
                }

        # Listen for battery updates
        async_dispatcher_connect(self.hass, UPDATE_BATTERY, self.async_update_battery)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self._attributes

    @property
    def native_value(self) -> RobotBatteryMap | CubeBatteryMap:
        """Return the state of the sensor."""
        return self._state


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
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

    sensors = [
        VectorBatterySensorEntity(coordinator, VectorBatterySensorFeature.ROBOT),
    ]

    async_add_entities(sensors, True)
