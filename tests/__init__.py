"""Tests for the Maytronics Skimmi integration."""

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from tests.components.bluetooth import generate_advertisement_data, generate_ble_device

MOCK_ADDRESS = "AA:BB:CC:DD:EE:FF"
MOCK_NAME = "SKIMMI_1234"

SKIMMI_DISCOVERY_INFO = BluetoothServiceInfoBleak(
    name=MOCK_NAME,
    address=MOCK_ADDRESS,
    rssi=-60,
    manufacturer_data={},
    service_uuids=[],
    service_data={},
    source="local",
    device=generate_ble_device(address=MOCK_ADDRESS, name=MOCK_NAME),
    advertisement=generate_advertisement_data(),
    time=0,
    connectable=True,
    tx_power=-127,
)
