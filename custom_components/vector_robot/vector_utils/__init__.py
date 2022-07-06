"""Vector utils used to fetch sentence data for Vector random speeches."""
from __future__ import annotations

from dataclasses import dataclass

from datetime import datetime
import json
import os
import logging
import random
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ha_vector import audio

from .const import BASE_URL, DATASETS, VectorDatasets
from .exceptions import VectorDatasetException

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

    def __init__(self, dataset_path: str):
        """Initialize the chatter object."""

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
        interval_min = dataset["min"]
        interval_max = dataset["max"]
        text = self.__substitute(dataset["sentence"][rand_line])

    def __substitute(self, text: str) -> str:
        """Substitute some strings."""
        _LOGGER.debug("Before substitution: %s", text)
        variations = self.__datasets[VectorDatasets.VARIATIONS]
        if "{name}" in text:
            if self.__last_seen["name"]:
                text = text.replace("{name}", self.__last_seen["name"])
            else:
                text = text.replace("{name}", "")

        for key, value in variations.items():
            # _LOGGER.debug("Key: %s\nValue: %s", key, value)
            args = {key: random.choice(value)}
            _LOGGER.debug(args)
            text = text.format(**args)

        _LOGGER.debug("After substitution: %s", text)
        return text


class DataRunner:
    """Data runner class."""

    def __init__(self, hass: HomeAssistant, save_path: str) -> None:
        """Initialize data runner object."""
        self.last_refresh: datetime = None
        self._client = async_get_clientsession(hass)
        self._save_path = f"{save_path}-datasets"

    async def async_refresh(self) -> None:
        """Refresh all datasets."""
        for data in DATASETS.items():
            if data[1]:
                _LOGGER.debug("Refreshing dataset %s", data[1])
                await self.__async_fetch_dataset(data[1])

    async def __async_fetch_dataset(self, filename: str) -> None:
        """Fetch dataset."""
        data_url = (BASE_URL).format(filename)
        res = await self._client.get(data_url)

        if res.status != 200:
            raise VectorDatasetException(f"Error fetching dataset from {data_url}")

        dataset = await res.json(content_type="text/plain")
        await self.__async_save_dataset(filename, dataset)

    async def __async_save_dataset(self, filename: str, dataset: Any) -> None:
        """Save dataset to local destination."""
        os.makedirs(str(self._save_path), exist_ok=True)
        fullname = str(f"{self._save_path}/{filename}")
        with os.fdopen(
            os.open(fullname, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666), "w"
        ) as file:
            json.dump(dataset, file)

    @property
    def path(self) -> str:
        """Returns the path to the datasets."""
        return self._save_path
