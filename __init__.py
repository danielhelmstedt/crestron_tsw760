"""Crestron TSW-760 integration for Home Assistant."""

import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PLATFORMS
from .coordinator import CrestronDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Crestron TSW-760 from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = config_entry.data
    coordinator = CrestronDataUpdateCoordinator(
        hass, config_entry.data[CONF_HOST], config_entry.data[CONF_NAME]
    )
    # Forward the setup to the appropriate platforms
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    # Forward the setup to the appropriate platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok


class CrestronEntity(CoordinatorEntity):
    """Representation of a Crestron entity."""

    def __init__(
        self,
        coordinator: CrestronDataUpdateCoordinator,
        name: str,
        value_path: list,
        entity_id: str,
        config_entry: config_entries.ConfigEntry,
    ):
        """Initialize the Crestron entity."""
        super().__init__(coordinator)
        self._attr_name = name
        self.value_path = value_path
        self._entity_id = entity_id
        self._attr_unique_id = f"{entity_id}_" + "_".join(value_path)
        self._attr_model = self.coordinator.data.get("model", "")
        self._attr_serial_number = self.coordinator.data.get("SerialNumber", "")
        self._attr_mac_address = self.coordinator.data.get("MacAddress", "")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_serial_number)},
            "name": config_entry.data.get(CONF_NAME, name),
            "manufacturer": "Crestron",
            "model": self._attr_model,
            "serial_number": self._attr_serial_number,
            "connections": {("mac", self._attr_mac_address)},
        }

    @property
    def device_info(self):
        """Return device information about this entity."""
        return self._attr_device_info

    @property
    def available(self):
        """Return if the entity is available."""
        return self.coordinator.last_update_success

    def _extract_value(self):
        """Extract value from the API response."""
        value = self.coordinator.data
        if value is None:
            return None
        for key in self.value_path:
            value = value.get(key)
            if value is None:
                return None
        return value
