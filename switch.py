"""Switch Component."""

import json
import logging

import aiohttp

from homeassistant.components.switch import SwitchEntity

from . import CrestronEntity
from .const import DOMAIN, ENTITIES_TO_EXPOSE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Docstring."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_id = entry.entry_id
    entities = [
        CrestronSwitch(
            coordinator,
            entity["name"],
            entity["value_path"],
            device_id,
        )
        for entity in ENTITIES_TO_EXPOSE
        if entity["type"] == "switch"
    ]
    async_add_entities(entities)


class CrestronSwitch(CrestronEntity, SwitchEntity):
    """Representation of a Crestron Switch entity."""

    def __init__(self, coordinator, name, value_path, device_id):
        """Initialize the CrestronSwitch entity."""
        super().__init__(coordinator, name, value_path, device_id)
        self._attr_name = name
        self._device_id = f"{name}_switch".replace(" ", "_").lower()
        self._attr_is_on = self._extract_value()

    @property
    def unique_id(self):
        """Return a unique ID for the entity."""
        return f"{self._device_id}_{self._attr_name}"

    @property
    def name(self):
        """Return the name of the entity."""
        return self._attr_name

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._attr_is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._attr_is_on = True
        await self.async_update_api(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        self._attr_is_on = False
        await self.async_update_api(False)
        self.async_write_ha_state()

    async def async_update_api(self, state: bool) -> None:
        """Update the API with the new switch state."""
        api_url = f"http://{self.coordinator.host}/Device"
        payload = self._create_payload(state)
        try:
            _LOGGER.debug("Setting state for %s to %s", self._attr_name, state)

            async with (
                aiohttp.ClientSession() as session,
                session.post(api_url, json=payload) as response,
            ):
                response.raise_for_status()
                # Fetch additional information from the device
                response_text = await response.text()
                _LOGGER.debug("Received device response: %s", response_text)
                response_data = json.loads(response_text, strict=False)

                _LOGGER.debug("Set state response: %s", response_data)
                await self._handle_response(response_data)

        except aiohttp.ClientError:
            _LOGGER.exception("Failed to set state for %s.", self._attr_name)

    def _create_payload(self, state: bool):
        """Create the payload for the API request."""
        payload = {}
        current_level = payload
        for key in self.value_path:
            current_level[key] = {}
            previous_level = current_level
            current_level = current_level[key]
        previous_level[self.value_path[-1]] = state
        return payload

    async def _handle_response(self, response_data):
        """Handle the response from the API."""
        for action in response_data.get("Actions", []):
            for result in action.get("Results", []):
                if result.get("StatusId") != 0:
                    _LOGGER.error(
                        "Failed to set property %s. Error: %s",
                        result.get("Property"),
                        result.get("StatusInfo"),
                    )
