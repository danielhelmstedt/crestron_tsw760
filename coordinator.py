"""Module that provides a DataUpdateCoordinator for fetching and updating data from a Crestron device."""

from datetime import timedelta
import json
import logging

import aiohttp

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

EXCLUDED_KEYS = ["CertificateStore", "Ieee8021x"]


def filter_response_data(data, excluded_keys):
    """Filter out specified keys from the response data."""
    if isinstance(data, dict):
        return {
            k: filter_response_data(v, excluded_keys)
            for k, v in data.items()
            if k not in excluded_keys
        }
    if isinstance(data, list):
        return [filter_response_data(item, excluded_keys) for item in data]
    return data


class CrestronDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Crestron data."""

    def __init__(self, hass, host, name):
        """Initialize the coordinator."""
        self.host = host
        super().__init__(
            hass, _LOGGER, name=name, update_interval=timedelta(seconds=30)
        )
        self.data = {}

    async def _async_update_data(self):
        """Fetch data from the API."""
        api_url = f"http://{self.host}/Device"
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(api_url) as response,
            ):
                response.raise_for_status()
                response_text = await response.text()
                _LOGGER.debug("Received device response: %s", response_text)
                response_data = json.loads(response_text, strict=False)
                filtered_data = filter_response_data(response_data, EXCLUDED_KEYS)
                _LOGGER.debug("Filtered response: %s", filtered_data)
                self.data = filtered_data
                self.data["model"] = get_nested_value(
                    response_data, ["Device", "DeviceInfo", "Model"], "Default Model"
                )
                self.data["SerialNumber"] = get_nested_value(
                    response_data,
                    ["Device", "DeviceInfo", "SerialNumber"],
                    "Default Serial Number",
                )
                self.data["MacAddress"] = get_nested_value(
                    response_data,
                    ["Device", "DeviceInfo", "MacAddress"],
                    "Default MAC Address",
                )
                return self.data
        except aiohttp.ClientError:
            _LOGGER.exception("Failed to fetch data from %s", self.host)
            raise

    async def async_update_api(self, value: str) -> None:
        """Update the API with the new EMS URL."""
        api_url = f"http://{self.host}/Device/ThirdPartyApplications"
        payload = {"Device": {"ThirdPartyApplications": {"Ems": {"ServerUrl": value}}}}

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(api_url, json=payload) as response,
            ):
                response.raise_for_status()
                _LOGGER.debug("Updated EMS URL to %s", value)
        except aiohttp.ClientError:
            _LOGGER.exception("Failed to update EMS URL to %s", value)
            raise


def get_nested_value(data, keys, default=None):
    """Retrieve a nested value from a dictionary."""
    for key in keys:
        data = data.get(key, default)
        if data is default:
            break
    return data
