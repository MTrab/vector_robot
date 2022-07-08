"""Stuff for making Vector speech easy to handle."""
# pylint: disable=bare-except
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from enum import Enum
import random

from .chatter import Chatter
from .const import VectorDatasets

_LOGGER = logging.getLogger(__name__)

# Sometimes speech doesn't work, lets try again MAX_ATTEMPTS times.
MAX_ATTEMPTS = 15


class VectorSpeachType(Enum):
    """Supported types of speach."""

    PASS = "pass"  # Do nothing
    CUSTOM = "custom"  # Custom text
    PETTING = "petting"  # When petting has started
    CLIFF = "cliff"  # When finding a "cliff" or other noticable color change
    GREETING = "greeting"  # Greeting
    DROP = "drop"  # When dropped or falling


class VectorSpeech:
    """Vector speech class."""

    __last = {}
    __dataset: str

    def __init__(self, robot, dataset) -> None:
        """Initialize a speech class."""
        self.robot = robot
        self.__dataset = dataset

    async def async_speak(
        self,
        text: str | None = None,
        predefined: VectorSpeachType = VectorSpeachType.CUSTOM,
        use_vector_voice: bool = True,
        speed: float = 1.0,
    ) -> None:
        """Routing for making Vector speak."""
        attempt = 0

        # If Vector is doing something, don't speak
        if self.robot.status.is_pathing is True:
            _LOGGER.debug("I'm busy, cannot speak now...")
            return

        # This adds a bit of controllable randomness to some of the random dialogues
        # (jokes, telling the time, etc.)
        if predefined == VectorSpeachType.PASS:
            _LOGGER.debug(
                "Instead of attempting a random comment, I chose to pass this time..."
            )
            return

        now = datetime.now()
        if predefined not in self.__last:
            self.__last[predefined] = {
                "last": now - timedelta(seconds=100),
                "next": now + timedelta(seconds=random.randint(2, 15)),
            }

        if now < self.__last[predefined]["next"]:
            return  # Too soon to speak again

        if predefined == VectorSpeachType.CUSTOM:
            to_say = text
            self.__last[predefined] = {
                "last": now,
                "next": now + timedelta(seconds=random.randint(2, 15)),
            }
        else:
            chatter = Chatter(self.__dataset)
            response = chatter.get_text(VectorDatasets.DIALOGS, predefined)
            to_say = response.text
            self.__last[predefined] = {
                "last": now,
                "next": now
                + timedelta(seconds=random.randint(response.min, response.max)),
            }

        while attempt < MAX_ATTEMPTS:
            attempt = attempt + 1

            try:
                await asyncio.wrap_future(self.robot.conn.request_control())
                await asyncio.wrap_future(
                    self.robot.behavior.say_text(
                        text=to_say,
                        use_vector_voice=use_vector_voice,
                        duration_scalar=speed,
                    )
                )
                await asyncio.wrap_future(self.robot.conn.release_control())
                return
            except:
                _LOGGER.debug(
                    "Couldn't get robot control. Trying to say '%s' again", to_say
                )
                await asyncio.sleep(1)

        if attempt == MAX_ATTEMPTS:
            _LOGGER.error("Couldn't persuade Vector to talk :(")
            await asyncio.wrap_future(self.robot.conn.release_control())
