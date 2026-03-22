"""Config flow for the Maytronics Skimmi integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection
import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_PASSWORD
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, UUID_HW_REVISION

_LOGGER = logging.getLogger(__name__)


async def validate_ble_device(
    ble_device: object,
    address: str,
) -> None:
    """Validate we can connect to the BLE device and read a characteristic."""
    try:
        client = await establish_connection(BleakClient, ble_device, address)
    except (BleakError, TimeoutError) as err:
        raise CannotConnect from err
    try:
        await client.read_gatt_char(UUID_HW_REVISION)
    except BleakError as err:
        raise CannotConnect from err
    finally:
        await client.disconnect()


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Maytronics Skimmi."""

    VERSION = 1
    MINOR_VERSION = 1

    _discovery_info: BluetoothServiceInfoBleak | None = None
    _reauth_entry: ConfigEntry | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=vol.Schema(
                {vol.Optional(CONF_PASSWORD, default=""): str}
            ),
            description_placeholders={"name": discovery_info.name},
        )

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm bluetooth discovery and create entry."""
        assert self._discovery_info is not None
        errors: dict[str, str] = {}

        if user_input is not None:
            address = self._discovery_info.address
            password = user_input.get(CONF_PASSWORD, "").strip() or None

            try:
                await validate_ble_device(self._discovery_info.device, address)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=self._discovery_info.name,
                    data={
                        CONF_ADDRESS: address,
                        CONF_PASSWORD: password,
                    },
                )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=vol.Schema(
                {vol.Optional(CONF_PASSWORD, default=""): str}
            ),
            description_placeholders={"name": self._discovery_info.name},
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick a discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            password = user_input.get(CONF_PASSWORD, "").strip() or None
            discovery = self._find_discovery(address)
            if discovery is None:
                return self.async_abort(reason="no_devices_found")

            try:
                await validate_ble_device(discovery.device, address)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=discovery.name or "Skimmi",
                    data={
                        CONF_ADDRESS: address,
                        CONF_PASSWORD: password,
                    },
                )

        current_addresses = self._async_current_ids()
        devices: dict[str, str] = {}
        for info in async_discovered_service_info(self.hass, connectable=True):
            if (
                info.address not in current_addresses
                and info.name
                and (
                    info.name.upper().startswith("SKIMMI")
                    or "SKIMLUX" in info.name.upper()
                )
            ):
                devices[info.address] = f"{info.name} ({info.address})"

        if not devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(devices),
                    vol.Optional(CONF_PASSWORD, default=""): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication when the device requires a password."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_PASSWORD): str}
            ),
        )

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthentication confirmation."""
        assert self._reauth_entry is not None

        if user_input is not None:
            return self.async_update_reload_and_abort(
                self._reauth_entry,
                data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
            )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_PASSWORD): str}
            ),
        )

    def _find_discovery(
        self, address: str
    ) -> BluetoothServiceInfoBleak | None:
        """Find a discovery info by address."""
        for info in async_discovered_service_info(self.hass, connectable=True):
            if info.address == address:
                return info
        return None


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
