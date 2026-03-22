"""Common fixtures for the Maytronics Skimmi tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.skimmi.const import DOMAIN
from homeassistant.const import CONF_ADDRESS, CONF_PASSWORD

from tests.common import MockConfigEntry

from . import MOCK_ADDRESS


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="SKIMMI_1234",
        data={
            CONF_ADDRESS: MOCK_ADDRESS,
            CONF_PASSWORD: None,
        },
        unique_id=MOCK_ADDRESS,
    )


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.skimmi.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
