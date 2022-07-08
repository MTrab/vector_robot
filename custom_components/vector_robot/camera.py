"""Vector robot cameras."""
from __future__ import annotations
import asyncio
import io

import logging

from homeassistant.components.camera import Camera, CameraEntityFeature, Image
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from PIL import Image as PILImage, ImageDraw

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def create_default_image(image_width, image_height, do_gradient=False):
    """Create a place-holder PIL image to use until we have a live feed from Vector"""
    image_bytes = bytearray([0x70, 0x70, 0x70]) * image_width * image_height

    if do_gradient:
        i = 0
        for y in range(image_height):
            for x in range(image_width):
                image_bytes[i] = int(255.0 * (x / image_width))  # R
                image_bytes[i + 1] = int(255.0 * (y / image_height))  # G
                image_bytes[i + 2] = 0  # B
                i += 3

    image = PILImage.frombytes(
        "RGB", (image_width, image_height), bytes(image_bytes)
    )
    return bytes(image.tobytes())


class VectorCamera(Camera):
    """A Vector robot camera."""

    def __init__(self, coordinator, enabled: bool = True) -> None:
        """Initialize a Vector camera entity."""
        self._last_image = create_default_image(320, 240)
        self._enabled = enabled
        self._coordinator = coordinator
        super().__init__()

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the camera image."""
        # self._coordinator.robot.camera.init_camera_feed()
        # img = await self._coordinator.hass.async_add_executor_job(
        #     self._coordinator.robot.camera.latest_image
        # )
        # self._last_image = img.convert("RGB")
        return self._last_image

    # async def stream_source(self) -> str | None:
    #     """Return the stream source."""


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Discover cameras on a UniFi Protect NVR."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([VectorCamera(coordinator)])
