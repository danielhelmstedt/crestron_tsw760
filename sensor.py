"""Sensor Component."""

from homeassistant.components.sensor import SensorEntity

from . import CrestronEntity
from .const import DOMAIN, ENTITIES_TO_EXPOSE


async def async_setup_entry(hass, entry, async_add_entities):
    """Docstring."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_id = entry.entry_id
    entities = [
        CrestronSensor(
            coordinator,
            entity["name"],
            entity["value_path"],
            device_id,
        )
        for entity in ENTITIES_TO_EXPOSE
        if entity["type"] == "sensor"
    ]
    async_add_entities(entities)


class CrestronSensor(CrestronEntity, SensorEntity):
    """Represenation of a Crestron Sensor entity."""

    def __init__(self, coordinator, name, value_path, device_id):
        """Initialize the CrestronSensor entity."""
        super().__init__(coordinator, name, value_path, device_id)
        self._attr_name = name
        self._device_id = f"{name}_sensor".replace(" ", "_").lower()
        self._attr_state = self._extract_value()

    @property
    def name(self):
        """Return the name of the entity."""
        return self._attr_name

    @property
    def unique_id(self):
        """Return a unique ID for the entity."""
        return f"{self._device_id}_{self._attr_name}"

    @property
    def state(self):
        """Extract the sensor's current value."""
        return self._extract_value()
