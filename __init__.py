"""The Maytronics Skimmi integration."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import SkimmiCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type SkimmiConfigEntry = ConfigEntry[SkimmiCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SkimmiConfigEntry) -> bool:
    """Set up Maytronics Skimmi from a config entry."""
    address: str = entry.data[CONF_ADDRESS]

    if not bluetooth.async_ble_device_from_address(hass, address, connectable=True):
        raise ConfigEntryNotReady(
            f"Could not find Skimmi device with address {address}"
        )

    coordinator = SkimmiCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SkimmiConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
