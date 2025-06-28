"""Button Component."""

import json
import logging
import aiohttp

from homeassistant.components.button import ButtonEntity

from . import CrestronEntity
from .const import DOMAIN, ENTITIES_TO_EXPOSE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Crestron button platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data.get("name", "default_name")

    entities = [
        CrestronButton(
            coordinator,
            f"{name} {entity['name']}",
            entity["value_path"],
            f"{name}_{entity['name']}".replace(" ", "_").lower(),
            config_entry,
        )
        for entity in ENTITIES_TO_EXPOSE
        if entity["type"] == "button"
    ]
    async_add_entities(entities)


class CrestronButton(CrestronEntity, ButtonEntity):
    """Representation of a Crestron momentary Button."""

    def __init__(self, coordinator, name, value_path, entity_id, config_entry):
        """Initialize the CrestronButton entity."""
        super().__init__(coordinator, name, value_path, entity_id, config_entry)
        self._attr_name = name
        self._entity_id = entity_id
        self._value_path = value_path

    @property
    def unique_id(self):
        """Return a unique ID for the button entity."""
        return f"{self._entity_id}_{self._attr_name}"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Button %s pressed", self._attr_name)
        api_url = f"http://{self.coordinator.host}/Device"
        payload = self._create_payload(True)  # Momentary press

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(api_url, json=payload) as response,
            ):
                response.raise_for_status()
                response_text = await response.text()
                _LOGGER.debug("Received device response: %s", response_text)
                response_data = json.loads(response_text, strict=False)
                await self._handle_response(response_data)

        except aiohttp.ClientError:
            _LOGGER.exception("Failed to send press for %s.", self._attr_name)

    def _create_payload(self, state: bool):
        """Create the payload for the API request."""
        payload = {}
        current_level = payload
        for key in self.value_path[:-1]:
            current_level[key] = {}
            current_level = current_level[key]
        current_level[self.value_path[-1]] = state
        return payload

    async def _handle_response(self, response_data):
        """Handle the response from the API."""
        for action in response_data.get("Actions", []):
            for result in action.get("Results", []):
                if result.get("StatusId") != 0:
                    _LOGGER.error(
                        "Failed to press button %s. Error: %s",
                        result.get("Property"),
                        result.get("StatusInfo"),
                    )
