"""Data coordinator for the Maytronics Skimmi integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
import logging
import struct

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BATTERY_LEVEL_MAP,
    DEVICE_STATE_MAP,
    DOMAIN,
    IDLE_COMMAND,
    UUID_AUTH_READ,
    UUID_AUTH_WRITE,
    UUID_CONTROL_WRITE,
    UUID_FW_REVISION,
    UUID_HW_REVISION,
    UUID_SERIAL_NUMBER,
    UUID_STATUS_NOTIFY,
    UUID_SW_REVISION,
)

_LOGGER = logging.getLogger(__name__)

POLL_INTERVAL = timedelta(seconds=30)
STATUS_TIMEOUT = 10.0


@dataclass
class SkimmiDeviceInfo:
    """Static device information read once from BLE characteristics."""

    serial_number: str | None = None
    hw_revision: str | None = None
    sw_revision: str | None = None
    fw_revision: str | None = None


@dataclass
class SkimmiStatus:
    """Dynamic device status parsed from BLE status notifications."""

    device_state: str = "idle"
    is_charging: bool = False
    power: float = 0.0
    battery_level: int = 0
    temperature: float | None = None
    cycle_time: int = 0
    motor_minutes: int = 0


@dataclass
class SkimmiData:
    """Combined device data returned by the coordinator."""

    status: SkimmiStatus = field(default_factory=SkimmiStatus)
    device_info: SkimmiDeviceInfo = field(default_factory=SkimmiDeviceInfo)


def compute_auth_response(challenge: bytes, password: str) -> bytes:
    """Compute BLE authentication response using XOR-based challenge-response."""
    pwd = (password + password).upper().encode("ascii")
    response = bytearray(12)
    response[0] = 10
    response[1] = 1
    response[3] = 1

    if len(pwd) < 8:
        return bytes(response)

    a = bytearray(8)
    a[0] = (pwd[0] ^ challenge[5]) & 0xFF
    a[1] = ((((a[0] + pwd[1]) & 0xFF) ^ challenge[1]) - 10) & 0xFF
    a[2] = ((((a[0] - pwd[3]) & 0xFF) ^ challenge[3]) - 5) & 0xFF
    a[3] = ((((a[2] + pwd[5]) & 0xFF) ^ challenge[2]) - 2) & 0xFF
    a[4] = ((((a[1] + pwd[2]) & 0xFF) ^ challenge[0]) + 9) & 0xFF
    a[5] = ((((a[4] - pwd[4]) & 0xFF) ^ challenge[4]) + 11) & 0xFF
    a[6] = ((((a[3] - pwd[7]) & 0xFF) ^ challenge[7]) - 6) & 0xFF
    a[7] = ((((a[6] + pwd[6]) & 0xFF) ^ challenge[6]) + 16) & 0xFF

    response[4:12] = a
    return bytes(response)


def parse_status(data: bytes) -> SkimmiStatus:
    """Parse status notification data from the device.

    Status byte layout (from APK reverse engineering):
      [0]     : reserved
      [1]     : reserved
      [2]     : device state (0=idle, 1=cleaning, 2=paused, 3+=error)
      [3]     : flags (bits 2-3 = charging)
      [4]     : reserved
      [5]     : power in tenths of watts
      [6]     : battery level (0-6)
      [7]     : filter status nibbles
      [8:10]  : temperature (big-endian signed short, tenths of °C)
      [10:12] : cycle time in minutes (big-endian unsigned short)
      [12:16] : motor minutes (big-endian unsigned int)
      [16]    : additional status
    """
    if len(data) < 17:
        return SkimmiStatus()

    device_state_raw = data[2]
    device_state = DEVICE_STATE_MAP.get(device_state_raw, "error")

    is_charging = (data[3] & 0x0C) > 0
    power = (data[5] & 0xFF) / 10.0
    battery_level_raw = data[6] & 0x0F
    battery_level = BATTERY_LEVEL_MAP.get(battery_level_raw, 0)

    temperature = struct.unpack(">h", bytes([data[8], data[9]]))[0] / 10.0

    cycle_time = ((data[10] & 0xFF) << 8) | (data[11] & 0xFF)
    motor_minutes = (
        ((data[12] & 0xFF) << 24)
        | ((data[13] & 0xFF) << 16)
        | ((data[14] & 0xFF) << 8)
        | (data[15] & 0xFF)
    )

    return SkimmiStatus(
        device_state=device_state,
        is_charging=is_charging,
        power=power,
        battery_level=battery_level,
        temperature=temperature,
        cycle_time=cycle_time,
        motor_minutes=motor_minutes,
    )


class SkimmiCoordinator(DataUpdateCoordinator[SkimmiData]):
    """Coordinator that polls a Skimmi device over BLE."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=POLL_INTERVAL,
        )
        self.address: str = config_entry.data[CONF_ADDRESS]
        self.password: str | None = config_entry.data.get(CONF_PASSWORD)
        self.device_info = SkimmiDeviceInfo()

    async def _async_update_data(self) -> SkimmiData:
        """Poll the device via BLE and return parsed data."""
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            raise UpdateFailed(
                f"Could not find Skimmi device with address {self.address}"
            )

        try:
            client = await establish_connection(
                BleakClient, ble_device, self.address
            )
        except (BleakError, TimeoutError) as err:
            raise UpdateFailed(f"Failed to connect: {err}") from err

        try:
            await self._authenticate(client)

            if self.device_info.serial_number is None:
                await self._read_device_info(client)

            status = await self._read_status(client)
        except (BleakError, TimeoutError) as err:
            raise UpdateFailed(f"Communication error: {err}") from err
        finally:
            await client.disconnect()

        return SkimmiData(status=status, device_info=self.device_info)

    async def _authenticate(self, client: BleakClient) -> None:
        """Handle BLE authentication handshake.

        The Skimmi uses a challenge-response authentication protocol:
        - Version >= 2 devices auto-pair (no password needed)
        - Older devices or password-protected devices require a password
        """
        try:
            auth_data = await client.read_gatt_char(UUID_AUTH_READ)
        except BleakError:
            _LOGGER.debug("No auth characteristic found, skipping authentication")
            return

        if len(auth_data) < 12:
            return

        version = auth_data[1]
        status = auth_data[3]

        if version >= 2 and status == 1:
            _LOGGER.debug("Auto-pair device (version %d), no auth needed", version)
            return

        if status == 2:
            _LOGGER.debug("Device already authenticated")
            return

        if status in (1, 4) and self.password:
            challenge = bytes(auth_data[4:12])
            auth_response = compute_auth_response(challenge, self.password)
            await client.write_gatt_char(
                UUID_AUTH_WRITE, auth_response, response=False
            )
            await asyncio.sleep(0.5)

            auth_data = await client.read_gatt_char(UUID_AUTH_READ)
            if auth_data[3] != 2:
                _LOGGER.warning("Authentication failed for device %s", self.address)

    async def _read_device_info(self, client: BleakClient) -> None:
        """Read static device information characteristics."""
        for uuid, attr in (
            (UUID_SERIAL_NUMBER, "serial_number"),
            (UUID_HW_REVISION, "hw_revision"),
            (UUID_SW_REVISION, "sw_revision"),
            (UUID_FW_REVISION, "fw_revision"),
        ):
            try:
                data = await client.read_gatt_char(uuid)
                setattr(
                    self.device_info,
                    attr,
                    data.decode("utf-8", errors="replace").strip("\x00"),
                )
            except BleakError:
                _LOGGER.debug("Could not read %s", attr)

    async def _read_status(self, client: BleakClient) -> SkimmiStatus:
        """Read device status by subscribing to notifications and sending idle command."""
        status_event = asyncio.Event()
        status_data = bytearray()

        def _notification_handler(_sender: object, data: bytearray) -> None:
            status_data.extend(data)
            status_event.set()

        await client.start_notify(UUID_STATUS_NOTIFY, _notification_handler)
        try:
            await client.write_gatt_char(
                UUID_CONTROL_WRITE, IDLE_COMMAND, response=False
            )
            async with asyncio.timeout(STATUS_TIMEOUT):
                await status_event.wait()
        finally:
            try:
                await client.stop_notify(UUID_STATUS_NOTIFY)
            except BleakError:
                pass

        return parse_status(bytes(status_data))
