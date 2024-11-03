"""Setup device via Home Assistant UI Config Flow."""

import json
import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CrestronTSW760ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Crestron TSW-760."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            name = user_input[CONF_NAME]

            # Validate the user input here
            try:
                async with (
                    aiohttp.ClientSession() as session,
                    session.get(f"http://{host}/Device") as response,
                ):
                    response.raise_for_status()
                    # Fetch additional information from the device
                    response_text = await response.text()
                    _LOGGER.debug("Received device response: %s", response_text)
                    device_info = json.loads(response_text, strict=False)

                # Extract necessary information from device_info
                serial_number = device_info.get("serial_number")
                model = device_info.get("model")

                # Create entry with the validated data
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: host,
                        CONF_NAME: name,
                        "serial_number": serial_number,
                        "model": model,
                    },
                )
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
