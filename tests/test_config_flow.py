"""Test the Maytronics Skimmi config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.components.skimmi.config_flow import CannotConnect
from homeassistant.components.skimmi.const import DOMAIN
from homeassistant.const import CONF_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry

from . import MOCK_ADDRESS, MOCK_NAME, SKIMMI_DISCOVERY_INFO


async def test_bluetooth_discovery(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test bluetooth discovery initiates config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SKIMMI_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "homeassistant.components.skimmi.config_flow.validate_ble_device",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: ""},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_NAME
    assert result["data"] == {
        CONF_ADDRESS: MOCK_ADDRESS,
        CONF_PASSWORD: None,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_bluetooth_discovery_with_password(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test bluetooth discovery with a password."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SKIMMI_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.skimmi.config_flow.validate_ble_device",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "1234"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_ADDRESS: MOCK_ADDRESS,
        CONF_PASSWORD: "1234",
    }


async def test_bluetooth_discovery_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test bluetooth discovery with connection error and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SKIMMI_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.skimmi.config_flow.validate_ble_device",
        side_effect=CannotConnect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: ""},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Recover from error
    with patch(
        "homeassistant.components.skimmi.config_flow.validate_ble_device",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: ""},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_NAME


async def test_bluetooth_discovery_already_configured(
    hass: HomeAssistant,
) -> None:
    """Test bluetooth discovery when device is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ADDRESS: MOCK_ADDRESS, CONF_PASSWORD: None},
        unique_id=MOCK_ADDRESS,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SKIMMI_DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_no_devices(hass: HomeAssistant) -> None:
    """Test user flow when no devices are found."""
    with patch(
        "homeassistant.components.skimmi.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_user_flow_with_devices(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test user flow with discovered devices."""
    with patch(
        "homeassistant.components.skimmi.config_flow.async_discovered_service_info",
        return_value=[SKIMMI_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(
            "homeassistant.components.skimmi.config_flow.async_discovered_service_info",
            return_value=[SKIMMI_DISCOVERY_INFO],
        ),
        patch(
            "homeassistant.components.skimmi.config_flow.validate_ble_device",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: MOCK_ADDRESS, CONF_PASSWORD: ""},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_NAME
    assert result["data"] == {
        CONF_ADDRESS: MOCK_ADDRESS,
        CONF_PASSWORD: None,
    }


async def test_user_flow_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test user flow with connection error and recovery."""
    with patch(
        "homeassistant.components.skimmi.config_flow.async_discovered_service_info",
        return_value=[SKIMMI_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM

    with (
        patch(
            "homeassistant.components.skimmi.config_flow.async_discovered_service_info",
            return_value=[SKIMMI_DISCOVERY_INFO],
        ),
        patch(
            "homeassistant.components.skimmi.config_flow.validate_ble_device",
            side_effect=CannotConnect,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: MOCK_ADDRESS, CONF_PASSWORD: ""},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Recover from error
    with (
        patch(
            "homeassistant.components.skimmi.config_flow.async_discovered_service_info",
            return_value=[SKIMMI_DISCOVERY_INFO],
        ),
        patch(
            "homeassistant.components.skimmi.config_flow.validate_ble_device",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: MOCK_ADDRESS, CONF_PASSWORD: ""},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
