"""Stuff for making Vector speech easy to handle."""
# pylint: disable=bare-except
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from enum import Enum
import random

from .chatter import Chatter
from .const import JOKE_ANIM, VectorDatasets

_LOGGER = logging.getLogger(__name__)

# Sometimes speech doesn't work, lets try again MAX_ATTEMPTS times.
MAX_ATTEMPTS = 5


class VectorSpeechType(Enum):
    """Supported types of Speech."""

    PASS = "pass"  # Do nothing
    CUSTOM = "custom"  # Custom text
    PETTING = "petting"  # When petting has started
    CLIFF = "cliff"  # When finding a "cliff" or other noticable color change
    GREETING = "greeting"  # Greeting
    DROP = "drop"  # When dropped or falling
    JOKE = "joke"  # Tell a random joke


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
        predefined: VectorSpeechType = VectorSpeechType.CUSTOM,
        use_vector_voice: bool = True,
        speed: float = 1.0,
        force_speech: bool = False,
    ) -> None:
        """Routing for making Vector speak."""
        attempt = 0
        _LOGGER.debug("Predefine called: %s", predefined)

        # If Vector is doing something, don't speak
        if self.robot.status.is_pathing is True:
            _LOGGER.debug("I'm busy, cannot speak now...")
            return

        # This adds a bit of controllable randomness to some of the random dialogues
        # (jokes, telling the time, etc.)
        if predefined == VectorSpeechType.PASS:
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

        if now < self.__last[predefined]["next"] and not force_speech:
            return  # Too soon to speak again

        if predefined == VectorSpeechType.CUSTOM:
            to_say = text
            self.__last[predefined] = {
                "last": now,
                "next": now + timedelta(seconds=random.randint(2, 15)),
            }
        elif predefined == VectorSpeechType.JOKE:
            chatter = Chatter(self.__dataset)
            response = chatter.get_text(VectorDatasets.JOKES)
            to_say = response.text
        else:
            chatter = Chatter(self.__dataset)
            response = chatter.get_text(VectorDatasets.DIALOGS, predefined.value)
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
                        duration_scalar=speed
                        if predefined != VectorSpeechType.JOKE
                        else 1.15,
                    )
                )

                if predefined == VectorSpeechType.JOKE:
                    if not isinstance(response.punchline, type(None)):
                        await asyncio.sleep(random.randint(response.min, response.max))
                        await asyncio.wrap_future(
                            self.robot.behavior.say_text(
                                text=response.punchline,
                                use_vector_voice=use_vector_voice,
                                duration_scalar=1.15,
                            )
                        )

                    try:
                        await asyncio.wrap_future(
                            self.robot.anim.play_animation_trigger(
                                random.choice(JOKE_ANIM)
                            )
                        )
                    except:
                        pass

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
