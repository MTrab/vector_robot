"""For handling the randominess in Vectors chatting and responses."""
from __future__ import annotations

import json
import logging
import os
import random
from dataclasses import dataclass

from ha_vector import audio

from .const import DATASETS, VectorDatasets

_LOGGER = logging.getLogger(__name__)


@dataclass
class ChatterResponse:
    """Dataclass for holding chatter response."""

    min: int
    max: int
    text: str


class Chatter:
    """Class for handling Vectors chatter."""

    # Muiltipliers for Vector's chattiness - used for manipulating the time delays
    __multiplier = {
        1: 7,
        2: 4,
        3: 2,
        4: 1.35,
        5: 1,
        6: 0.8,
        7: 0.5,
        8: 0.35,
        9: 0.2,
        10: 0.1,
    }

    __last_seen: dict = {"name": None, "time": None}

    __chattiness = __multiplier[5]

    # SDK volume mappings
    __vol = {
        1: audio.RobotVolumeLevel.LOW,
        2: audio.RobotVolumeLevel.MEDIUM_LOW,
        3: audio.RobotVolumeLevel.MEDIUM,
        4: audio.RobotVolumeLevel.MEDIUM_HIGH,
        5: audio.RobotVolumeLevel.HIGH,
    }

    __datasets = {}

    def __init__(self, dataset_path: str, chattiness: int = 5, volume: int = 4):
        """Initialize the chatter object."""

        self.__chattiness = self.__multiplier[chattiness]
        self._volume = self.__vol[volume]

        for data in DATASETS.items():
            if data[1]:
                _LOGGER.debug("Loading dataset %s", data[1])
                fullname = str(f"{dataset_path}/{data[1]}")
                with os.fdopen(os.open(fullname, os.O_RDONLY), "r") as file:
                    res = json.load(file)

                self.__datasets.update({data[0]: res})

    def get_text(self, data_type: VectorDatasets, event: str) -> ChatterResponse:
        """Get random text response."""
        dataset = self.__datasets[data_type][event]

        rand_line = random.randrange(0, len(dataset["sentence"]))
        interval_min = dataset["min"] * self.__chattiness
        interval_max = dataset["max"] * self.__chattiness
        text = self.__substitute(dataset["sentence"][rand_line])
        return ChatterResponse(interval_min, interval_max, text)

    def __substitute(self, text: str) -> str:
        """Substitute some strings."""
        _LOGGER.debug("Before substitution: %s", text)
        variations = self.__datasets[VectorDatasets.VARIATIONS]
        if "{name}" in text:
            if self.__last_seen["name"]:
                text = text.replace("{name}", self.__last_seen["name"])
            else:
                text = text.replace("{name}", "")

        text = text.format(
            good=random.choice(variations["good"]),
            scary=random.choice(variations["scary"]),
            weird=random.choice(variations["weird"]),
            interesting=random.choice(variations["interesting"]),
        )
        _LOGGER.debug("After substitution: %s", text)
        return text
