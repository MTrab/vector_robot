"""Stuff for making Vector speech easy to handle."""
# pylint: disable=bare-except
from __future__ import annotations
import asyncio

from datetime import datetime, timedelta
import logging
from enum import Enum
import random

from . import VectorHandler, VectorSpeechText

from .chatter import Chatter
from .const import JOKE_ANIM, JOKE_SPEED, VectorDatasets

_LOGGER = logging.getLogger(__name__)


class VectorSpeechType(Enum):
    """Supported types of Speech."""

    PASS = "pass"  # Do nothing
    CUSTOM = "custom"  # Custom text
    PETTING = "petting"  # When petting has started
    CLIFF = "cliff"  # When finding a "cliff" or other noticable color change
    GREETING = "greeting"  # Greeting
    DROP = "drop"  # When dropped or falling
    JOKE = "joke"  # Tell a random joke
    WAKE_WORD = "wake_word"  # When wake word (Hey Vector) was heard
    INVALID = "invalid"  # When Vector doesn't understand what he was told/asked


class VectorSpeech:
    """Vector speech class."""

    __last = {}
    __dataset: str

    def __init__(self, robot: VectorHandler, dataset) -> None:
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
        _LOGGER.debug("Predefine called: %s", predefined)

        # This adds a bit of controllable randomness to some of the random dialogues
        # (jokes, telling the time, etc.)
        if predefined == VectorSpeechType.PASS:
            _LOGGER.debug(
                "Instead of attempting a random comment, I chose to pass this time..."
            )
            return

        to_say = list[VectorSpeechText]
        now = datetime.now()
        if predefined not in self.__last:
            self.__last[predefined] = {
                "last": now - timedelta(seconds=100),
                "next": now + timedelta(seconds=random.randint(2, 15)),
            }

        if now < self.__last[predefined]["next"] and not force_speech:
            return  # Too soon to speak again

        if predefined == VectorSpeechType.CUSTOM:
            msg = VectorSpeechText()
            msg.Text = text
            msg.Speed = speed
            msg.Vector_Voice = use_vector_voice
            to_say.append(msg)

            self.__last[predefined] = {
                "last": now,
                "next": now + timedelta(seconds=random.randint(2, 15)),
            }
        elif predefined == VectorSpeechType.JOKE:
            chatter = Chatter(self.__dataset)
            response = chatter.get_text(VectorDatasets.JOKES)
            framing = VectorSpeechText()
            framing.Text = response.text
            framing.Speed = JOKE_SPEED
            framing.Vector_Voice = use_vector_voice
            to_say.append(framing)

            if not isinstance(response.punchline, type(None)):
                punchline = VectorSpeechText()
                punchline.Text = response.text
                punchline.Delay = random.randint(response.min, response.max)
                punchline.Speed = JOKE_SPEED
                punchline.Vector_Voice = use_vector_voice
                to_say.append(punchline)

        else:
            chatter = Chatter(self.__dataset)
            response = chatter.get_text(VectorDatasets.DIALOGS, predefined.value)
            msg = VectorSpeechText()
            msg.Text = response.text
            msg.Speed = speed
            msg.Vector_Voice = use_vector_voice
            to_say.append(msg)

            self.__last[predefined] = {
                "last": now,
                "next": now
                + timedelta(seconds=random.randint(response.min, response.max)),
            }

        await self.robot.async_speak(
            messages=to_say,
            use_vector_voice=use_vector_voice,
            speed=speed if predefined != VectorSpeechType.JOKE else 1.15,
        )

        if predefined == VectorSpeechType.JOKE:
            try:
                await asyncio.wrap_future(
                    self.robot.anim.play_animation_trigger(random.choice(JOKE_ANIM))
                )
            except:
                pass
