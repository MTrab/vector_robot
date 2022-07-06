"""Helper to handle config and certificate storage"""
from __future__ import annotations
from typing import Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers import storage

from ..const import DOMAIN

STORAGE_VERSION = 1
STORAGE_KEY: Final = DOMAIN


class VectorStore(storage.Store):
    """Definition of Vector Storage."""

    def __init__(self, hass: HomeAssistant, name: str) -> None:
        super().__init__(hass, STORAGE_VERSION, f"{STORAGE_KEY}/{name}")
        self._name = name

    async def _async_migrate_func(self, old_major_version, old_minor_version, old_data):
        return await super()._async_migrate_func(
            old_major_version, old_minor_version, old_data
        )

    @property
    def cert_path(self) -> str:
        """Get the certificate path."""
        return self.path.replace(self._name, "certs")
