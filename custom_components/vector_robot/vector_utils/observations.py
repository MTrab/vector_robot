"""Handler for Vectors observations."""
# pylint: disable=invalid-name
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


class Face:
    """Face definition."""

    __id: int
    __name: str
    __last_seen: float

    def __init__(self, face_id: int, name: str, last_seen: float):
        """Vector saw a know face."""
        self.__id = face_id
        self.__name = name
        self.__last_seen = last_seen

    @property
    def face_id(self) -> int:
        """Returns the face ID."""
        return self.__id

    @property
    def name(self) -> str:
        """Return the name of the face."""
        return self.__name

    @property
    def last_seen(self) -> int:
        """Return timestamp for when the face was last seen."""
        return self.__last_seen


class Observation:
    """Class for holding the observations done by Vector"""

    def __init__(self) -> None:
        """Initialize the observations class."""
        super().__init__()

        self.faces = {}
        self.objects = []
