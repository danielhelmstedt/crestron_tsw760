import logging
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PLATFORMS
from .coordinator import CrestronDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up the Crestron integration from a config entry."""
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        return False  # Prevent duplicate devices

    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    coordinator = CrestronDataUpdateCoordinator(hass, host, name)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Register platforms
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class CrestronEntity(CoordinatorEntity):
    """Representation of a Crestron entity."""

    def __init__(
        self,
        coordinator: CrestronDataUpdateCoordinator,
        name: str,
        value_path: list,
        device_id: str,
    ):
        """Initialize the Crestron entity."""
        super().__init__(coordinator)
        self._attr_name = name
        self.value_path = value_path
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_" + "_".join(value_path)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": name,
            "manufacturer": "Crestron",
            "model": "TSW-760",
        }

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
