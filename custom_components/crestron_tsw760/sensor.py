"""Sensor Component."""

from homeassistant.components.sensor import SensorEntity

from . import CrestronEntity
from .const import DOMAIN, ENTITIES_TO_EXPOSE


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Docstring."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data.get("name", "default_name")
    entities = [
        CrestronSensor(
            coordinator,
            f"{name} {entity['name']}",
            entity["value_path"],
            f"{name}_{entity['name']}".replace(" ", "_").lower(),
            config_entry,
        )
        for entity in ENTITIES_TO_EXPOSE
        if entity["type"] == "sensor"
    ]
    async_add_entities(entities, update_before_add=True)


class CrestronSensor(CrestronEntity, SensorEntity):
    """Represenation of a Crestron Sensor entity."""

    def __init__(
        self,
        coordinator,
        name,
        value_path,
        entity_id,
        config_entry,
    ):
        """Initialize the CrestronSensor entity."""
        super().__init__(coordinator, name, value_path, entity_id, config_entry)
        self._attr_name = name
        self._entity_id = entity_id
        self._value_path = value_path
        self._attr_state = self._extract_value()

    @property
    def unique_id(self):
        """Return a unique ID for the entity."""
        return f"{self._entity_id}_{self._attr_name}"

    @property
    def name(self):
        """Return the name of the entity."""
        return self._attr_name

    @property
    def state(self):
        """Extract the sensor's current value."""
        return self._extract_value()
