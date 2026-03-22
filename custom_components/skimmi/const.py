"""Constants for the Maytronics Skimmi integration."""

DOMAIN = "skimmi"

# Custom BLE Characteristic UUIDs
UUID_SETUP_WRITE = "00000010-0000-0000-0001-000000000001"
UUID_DEVICE_INFO = "00000010-0000-0000-0001-000000000002"
UUID_STATUS_NOTIFY = "00000010-0000-0000-0001-000000000004"
UUID_CONTROL_WRITE = "00000010-0000-0000-0001-000000000005"
UUID_AUTH_WRITE = "00000010-0000-0000-0001-000000000007"
UUID_AUTH_READ = "00000010-0000-0000-0001-000000000008"
UUID_SETTINGS_NOTIFY = "00000010-0000-0000-0001-000000000009"
UUID_MT_SERIAL = "00000010-0000-0000-0001-100000000001"

# Standard BLE Characteristic UUIDs (Device Information Service)
UUID_SERIAL_NUMBER = "00002a25-0000-1000-8000-00805f9b34fb"
UUID_HW_REVISION = "00002a27-0000-1000-8000-00805f9b34fb"
UUID_SW_REVISION = "00002a28-0000-1000-8000-00805f9b34fb"
UUID_FW_REVISION = "00002a26-0000-1000-8000-00805f9b34fb"

# BLE idle/poll command (20 bytes): requests status without changing device behavior
IDLE_COMMAND = bytes(
    [5, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
)

# Battery level raw value (0-6) to percentage mapping
BATTERY_LEVEL_MAP: dict[int, int] = {
    0: 0,
    1: 25,
    2: 50,
    3: 75,
    4: 100,
    5: 100,
    6: 100,
}

# Device state byte to string mapping
DEVICE_STATE_MAP: dict[int, str] = {
    0: "idle",
    1: "cleaning",
    2: "paused",
    9: "idle",
}
