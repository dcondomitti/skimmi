"""Sensor platform for the Maytronics Skimmi integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SkimmiConfigEntry
from .coordinator import SkimmiCoordinator, SkimmiData
from .entity import SkimmiEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SkimmiSensorEntityDescription(SensorEntityDescription):
    """Describes a Skimmi sensor entity."""

    value_fn: Callable[[SkimmiData], float | int | str | None]


SENSOR_DESCRIPTIONS: tuple[SkimmiSensorEntityDescription, ...] = (
    SkimmiSensorEntityDescription(
        key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.status.battery_level,
    ),
    SkimmiSensorEntityDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.status.temperature,
    ),
    SkimmiSensorEntityDescription(
        key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.status.power,
    ),
    SkimmiSensorEntityDescription(
        key="device_state",
        translation_key="device_state",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "cleaning", "paused", "error"],
        value_fn=lambda data: data.status.device_state,
    ),
    SkimmiSensorEntityDescription(
        key="motor_hours",
        translation_key="motor_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: round(data.status.motor_minutes / 60, 1),
    ),
    SkimmiSensorEntityDescription(
        key="cycle_time",
        translation_key="cycle_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.status.cycle_time,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkimmiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Skimmi sensor entities from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        SkimmiSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class SkimmiSensor(SkimmiEntity, SensorEntity):
    """Representation of a Skimmi sensor."""

    entity_description: SkimmiSensorEntityDescription

    def __init__(
        self,
        coordinator: SkimmiCoordinator,
        description: SkimmiSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"

    @property
    def native_value(self) -> float | int | str | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
