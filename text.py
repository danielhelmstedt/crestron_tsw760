"""Input URL to display on Crestron TSW-760."""

import json
import logging
import re

import aiohttp

from homeassistant.components.input_text import (
    CONF_MAX,
    CONF_MIN,
    CONF_MODE,
    CONF_PATTERN,
    InputText,
)
from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CrestronEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass, entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the CrestronText entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    name = "EMS URL"
    device_id = entry.entry_id
    entities = [CrestronEMSUrl(coordinator, name, device_id)]
    async_add_entities(entities)


class CrestronEMSUrl(CrestronEntity, InputText):
    """Representation of a Crestron EMS URL entity."""

    def __init__(self, coordinator, name, device_id):
        """Initialize the CrestronEMSUrl entity."""
        super().__init__(coordinator, name, [], device_id)
        self._config = {
            CONF_NAME: name,
            CONF_ICON: "mdi:link-variant",
            CONF_MIN: 0,
            CONF_MAX: 255,
            CONF_MODE: "text",
            CONF_PATTERN: r"(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})(\.[a-zA-Z0-9]{2,})?",
        }
        self._attr_name = self._config[CONF_NAME]
        self._attr_icon = self._config[CONF_ICON]
        self._attr_min = self._config[CONF_MIN]
        self._attr_max = self._config[CONF_MAX]
        self._attr_mode = self._config[CONF_MODE]
        self._attr_pattern = self._config[CONF_PATTERN]
        self.pattern_cmp = (
            re.compile(self._attr_pattern) if self._attr_pattern else None
        )
        self._current_value = ""
        self.editable = True
        self._current_value = self._extract_ems_url()

    def _extract_ems_url(self):
        """Extract the EMS URL from the coordinator's data."""
        value = self.coordinator.data
        if value is None:
            return ""
        for key in ["Device", "ThirdPartyApplications", "Ems", "ServerUrl"]:
            value = value.get(key)
            if value is None:
                return ""
        return value

    @property
    def unique_id(self):
        """Return a unique ID for the entity."""
        return f"{self._device_id}_{self._attr_name}"

    @property
    def name(self):
        """Return the name of the entity."""
        return self._attr_name

    @property
    def icon(self):
        """Return the icon of the entity."""
        return self._attr_icon

    @property
    def min(self):
        """Return the minimum length of the text."""
        return self._attr_min

    @property
    def max(self):
        """Return the maximum length of the text."""
        return self._attr_max

    @property
    def state(self):
        """Return the state of the entity."""
        return self._current_value

    async def async_set_value(self, value: str) -> None:
        """Set the value and update the API."""
        self._current_value = value
        await self.async_update_api(value)
        self.async_write_ha_state()

    async def async_update_api(self, value: str) -> None:
        """Update the API with the new EMS URL."""
        coordinator = self.coordinator
        api_url = f"http://{coordinator.host}/Device/ThirdPartyApplications"
        payload = {"Device": {"ThirdPartyApplications": {"Ems": {"ServerUrl": value}}}}

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(api_url, json=payload) as response,
            ):
                response.raise_for_status()
                # Fetch additional information from the device
                response_text = await response.text()
                _LOGGER.debug("Received device response: %s", response_text)
                response_data = json.loads(response_text, strict=False)

                actions = response_data.get("Actions", [])
                for action in actions:
                    results = action.get("Results", [])
                    for result in results:
                        if (
                            result.get("Path") == "Device.ThirdPartyApplications.Ems"
                            and result.get("Property") == "ServerUrl"
                            and result.get("StatusId") == 1
                        ):
                            _LOGGER.info(
                                "Successfully updated EMS URL: %s",
                                result.get("StatusInfo"),
                            )
                            return
                _LOGGER.error("Failed to update EMS URL: Unexpected response format")
        except aiohttp.ClientError as e:
            _LOGGER.error("Failed to update EMS URL: %s", e)
