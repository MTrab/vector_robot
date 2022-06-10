"""Helper classes for Vector integration."""
from __future__ import annotations
from enum import IntEnum

import logging

from .const import BATTERYMAP_TO_STATE

_LOGGER = logging.getLogger(__name__)


class RobotBatteryMap(IntEnum):
    """Robot level map."""

    UNKNOWN = 0  # Unknown level
    LOW = 1  # 3.6V or less. If on charger, 4V or less.
    NORMAL = 2  # Normal operating levels.
    FULL = 3  # This state can only be achieved when Vector is on the charger


class CubeBatteryMap(IntEnum):
    """Cube level map."""

    UNKNOWN = 0  # Unknown level
    LOW = 1  # 1.1V or less.
    NORMAL = 2  # Normal operating levels.


class BatteryBase:
    """Generic battery information."""

    def __init__(
        self, voltage=0, level: RobotBatteryMap | CubeBatteryMap = None
    ) -> None:
        """Initialize a base class."""
        self._voltage = voltage
        self._level = level

    @property
    def voltage(self) -> str:
        """Return voltage."""
        return self._voltage

    @property
    def level(self) -> str:
        """Return voltage."""
        return BATTERYMAP_TO_STATE[self._level]


class CubeBatteryInfo(BatteryBase):
    """Cube battery info class."""

    def __init__(
        self,
        voltage=None,
        level: CubeBatteryMap = CubeBatteryMap.UNKNOWN,
        last_reading=None,
        factory_id=None,
    ) -> None:
        """Initialize cube battery class."""
        super().__init__(voltage, level)

        self._last_reading = last_reading
        self._factory_id = factory_id


    @property
    def last_reading(self) -> str:
        """Return last reading."""
        return self._last_reading

    @property
    def factory_id(self) -> str:
        """Return cube factory id."""
        return self._factory_id

    def update(self, voltage, level: CubeBatteryMap, last_reading, factory_id) -> None:
        """Update cube battery states."""
        self._voltage = voltage
        self._level = level
        self._last_reading = last_reading
        self._factory_id = factory_id


class RobotBatteryInfo(BatteryBase):
    """Robot battery info class."""

    def __init__(
        self,
        voltage=None,
        level: RobotBatteryMap = RobotBatteryMap.UNKNOWN,
        charging=False,
        on_charger=False,
        suggested_charge_time=None,
    ) -> None:
        """Initialize robot battery class."""
        super().__init__(voltage, level)

        self._charging = charging
        self._on_charger = on_charger
        self._suggested_charge_time = suggested_charge_time


    @property
    def is_charging(self) -> bool:
        """Return true if charging."""
        return bool(self._charging)

    @property
    def on_charger(self) -> bool:
        """Return true if Vector is on charging platform."""
        return bool(self._on_charger)

    @property
    def suggested_charge_time(self) -> str:
        """Return suggested charge time."""
        return bool(self._suggested_charge_time)

    def update(
        self,
        voltage,
        level: RobotBatteryMap,
        charging,
        on_charger,
        suggested_charge_time,
    ) -> None:
        """Update cube battery states."""
        self._voltage = voltage
        self._level = level
        self._charging = charging
        self._on_charger = on_charger
        self._suggested_charge_time = suggested_charge_time
