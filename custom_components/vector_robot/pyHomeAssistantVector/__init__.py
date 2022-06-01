"""SDK for programming with the Digital Dream Labs / Anki Vector robot."""

import logging
import sys

from . import messaging
from .robot import AsyncRobot, Robot
from .version import __version__
from .api import API as api

logger = logging.getLogger("vector")  # pylint: disable=invalid-name

if sys.version_info < (3, 6, 1):
    sys.exit("vector requires Python 3.6.1 or later")

__all__ = ["Robot", "AsyncRobot", "logger", "messaging", "__version__", "api"]
