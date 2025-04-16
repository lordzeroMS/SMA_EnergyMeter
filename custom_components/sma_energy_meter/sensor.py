"""Support for SMA Energy Meter sensors."""
import logging

from homeassistant.components.sensor import (
    SensorEntity, SensorDeviceClass, SensorStateClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up sensors from config."""
    if discovery_info is None:
        return

    coordinator = hass.data[DOMAIN]

    # Wait for initial data
    await coordinator.async_config_entry_first_refresh()

    # Create sensors for all detected meters
    entities = []
    for serial in coordinator.get_all_serials():
        entities.extend(_create_sensors_for_meter(coordinator, serial))

    if entities:
        async_add_entities(entities)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Create entities dynamically based on coordinator data
    @callback
    def _add_new_meters():
        """Add sensors for newly discovered meters."""
        entities = []
        for serial in coordinator.get_all_serials():
            # Check if this meter already has sensors
            if serial not in _discovered_meters:
                _discovered_meters.add(serial)
                entities.extend(_create_sensors_for_meter(coordinator, serial))

        if entities:
            async_add_entities(entities)

    # Keep track of discovered meter serials
    _discovered_meters = set()

    # Register listener to add new meters
    entry.async_on_unload(coordinator.async_add_listener(_add_new_meters))

    # Initial device discovery
    _add_new_meters()

def _create_sensors_for_meter(coordinator, serial):
    """Create sensor entities for a meter."""
    entities = []
    meter_data = coordinator.get_meter_data(serial)

    if not meter_data:
        return entities

    for k, v in meter_data.items():
        # Skip unit definitions and serial
        if k.endswith('unit') or k == 'serial':
            continue

        unit = meter_data.get(k + 'unit', None)
        entities.append(SMAEnergyMeterSensor(coordinator, serial, k, unit))

    return entities

class SMAEnergyMeterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SMA Energy Meter sensor."""

    def __init__(self, coordinator, serial, key, unit):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial = serial
        self._key = key
        self._unit = unit

        # Get meter data for device info
        meter_data = coordinator.get_meter_data(serial)

        # Set entity ID and name
        self._attr_name = f"SMA {serial} {key}"
        self._attr_unique_id = f"sma_em_{serial}_{key}"

        # Set appropriate device class
        if unit is None:
            self._attr_device_class = None
        elif unit in ('V'):
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif unit == 'W':
            self._attr_device_class = SensorDeviceClass.POWER
        elif unit == 'A':
            self._attr_device_class = SensorDeviceClass.CURRENT
        elif unit in ('VA', 'VAr'):
            self._attr_device_class = SensorDeviceClass.APPARENT_POWER
        elif unit == 'Hz':
            self._attr_device_class = SensorDeviceClass.FREQUENCY
        elif unit in ('Wh', 'kWh', 'kVArh', 'kVAh'):
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

        # Set device info
        firmware = meter_data.get('speedwire-version', '').split('|')[0] if meter_data and 'speedwire-version' in meter_data else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"sma-em-{serial}")},
            name=f"SMA Energy Meter {serial}",
            manufacturer="SMA",
            model="Energy Meter",
            sw_version=firmware,
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        meter_data = self.coordinator.get_meter_data(self._serial)
        if meter_data:
            return meter_data.get(self._key)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit