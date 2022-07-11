"""Vector robot cameras."""
from __future__ import annotations
import asyncio
from enum import IntEnum
import io
from lib2to3.pytree import convert

import logging

from homeassistant.components.camera import (
    Camera,
    CameraEntityDescription,
    CameraEntityFeature,
    Image,
    ENTITY_ID_FORMAT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from PIL import Image as PILImage, ImageDraw
from ha_vector.events import Events

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class VectorCameraFeature(IntEnum):
    """Different camera types."""

    MAIN_CAM = 0
    NAV_MAP = 1


CAMERAS = [
    CameraEntityDescription(
        key=VectorCameraFeature.MAIN_CAM,
        name="Vision",
    )
]


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

    image = convert_pil_image_to_byte_array(
        PILImage.frombytes("RGB", (image_width, image_height), bytes(image_bytes))
    )
    return image


def convert_pil_image_to_byte_array(img):
    """Convert a PIL to bytes."""
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format="JPEG", subsampling=0, quality=100)
    img_byte_array = img_byte_array.getvalue()
    return img_byte_array


class VectorCamera(Camera):
    """A Vector robot camera."""

    entity_description: CameraEntityDescription

    def __init__(
        self, coordinator, description: CameraEntityDescription, enabled: bool = True
    ) -> None:
        """Initialize a Vector camera entity."""
        self._last_image = create_default_image(640, 360, True)
        self._enabled = enabled
        self.coordinator = coordinator
        self.robot = self.coordinator.robot
        self.entity_description = description
        self._attr_name = self.entity_description.name
        self.entity_id = (
            ENTITY_ID_FORMAT.format(f"{coordinator.name}_{description.name}")
            .replace("-", "_")
            .lower()
        )

        def on_image(robot, event_type, event, done=None):
            """Called when Vector receives a new image."""
            _LOGGER.debug("Got new image from Vector")
            self._last_image=convert_pil_image_to_byte_array(event.image.raw_image)

        self.robot.events.subscribe(on_image, Events.new_raw_camera_image)
        self.robot.events.subscribe(on_image, Events.new_camera_image)

        super().__init__()

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the camera image."""
        # await asyncio.wrap_future(self.robot.conn.request_control())
        # image = await asyncio.wrap_future(self.robot.camera.capture_single_image())
        # await asyncio.wrap_future(self.robot.conn.release_control())
        # self._last_image = io.BytesIO(image.raw_image)
        # img =await asyncio.wrap_future(self.robot.camera.latest_image)
        # _LOGGER.debug(img)
        # self._last_image = convert_pil_image_to_byte_array(img)

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

    entities = []
    for camera in CAMERAS:
        constructor = VectorCamera(coordinator, camera)

        entities.append(constructor)

    async_add_entities(entities, True)
