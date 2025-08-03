from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class UniFiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="UniFi Network Monitor", data=user_input)

        data_schema = vol.Schema({
            vol.Required("host"): str,
            vol.Required("api_key"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

class UniFiController:
    def __init__(self, host: str, api_key: str):
        self._host = host.replace("https://", "").replace("http://", "")
        self._api_key = api_key
        self.site_name = None
        self.devices = []

    async def update_data(self):
        # Get site name
        url = f"https://{self._host}/proxy/network/integration/v1/sites"
        headers = {
            "X-API-KEY": self._api_key,
            "Accept": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, ssl=False) as resp:
                    if resp.status == 200:
                        full_data = await resp.json()
                        _LOGGER.debug("UniFi API response data: %s", full_data)
                        data_list = full_data.get("data", [])
                        self.site_name = data_list[0]["name"] if data_list else "Unknown"
                    else:
                        self.site_name = f"HTTP Error: {resp.status}"
                        _LOGGER.error("UniFi API returned HTTP %d", resp.status)
                        return
        except Exception as e:
            self.site_name = f"Connection Error: {str(e)}"
            _LOGGER.error("Exception fetching UniFi data: %s", e)
            return

        # Now fetch devices for the site
        if not self.site_name or self.site_name.startswith("HTTP Error") or self.site_name.startswith("Connection Error"):
            return

        devices_url = f"https://{self._host}/proxy/network/api/s/{self.site_name}/stat/device"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(devices_url, headers=headers, ssl=False) as resp:
                    if resp.status == 200:
                        devices_data = await resp.json()
                        self.devices = devices_data.get("data", [])
                        _LOGGER.debug("Fetched %d devices", len(self.devices))
                    else:
                        _LOGGER.error("Failed to fetch devices: HTTP %d", resp.status)
                        self.devices = []
        except Exception as e:
            _LOGGER.error("Exception fetching UniFi devices: %s", e)
            self.devices = []
