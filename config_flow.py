"""Setup device via Home Assistant UI Config Flow."""

import json
import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_nested_value(data, keys, default=None):
    """Retrieve a nested value from a dictionary."""
    for key in keys:
        data = data.get(key, default)
        if data is default:
            break
    return data


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
                    model = get_nested_value(
                        device_info, ["Device", "DeviceInfo", "Model"], ""
                    )
                    serial_number = get_nested_value(
                        device_info, ["Device", "DeviceInfo", "SerialNumber"], ""
                    )
                    mac_address = get_nested_value(
                        device_info, ["Device", "DeviceInfo", "MacAddress"], ""
                    )

                # Create entry with the validated data
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: host,
                        CONF_NAME: name,
                        "model": model,
                        "serial_number": serial_number,
                        "mac_address": mac_address,
                    },
                )
            except aiohttp.ClientError as err:
                _LOGGER.error("Error connecting to device: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_NAME): str,
                }
            ),
            errors=errors,
        )
