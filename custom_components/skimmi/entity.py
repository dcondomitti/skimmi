"""Base entity for the Maytronics Skimmi integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SkimmiCoordinator


class SkimmiEntity(CoordinatorEntity[SkimmiCoordinator]):
    """Base entity for Skimmi devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SkimmiCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            identifiers={(DOMAIN, coordinator.address)},
            name=coordinator.config_entry.title,
            manufacturer="Maytronics",
            model="Skimmi",
            sw_version=coordinator.device_info.sw_revision,
            hw_version=coordinator.device_info.hw_revision,
            serial_number=coordinator.device_info.serial_number,
        )
