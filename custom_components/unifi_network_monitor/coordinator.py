# custom_components/unifi_network_monitor/coordinator.py

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
import logging
import aiohttp
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=1)

class UniFiDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession, config_data: dict):
        super().__init__(
            hass,
            _LOGGER,
            name="UniFi Network Monitor",
            update_interval=SCAN_INTERVAL,
        )
        self.session = session
        self.api_key = config_data["api_key"]
        self.url = config_data["base_url"].rstrip("/") + "/proxy/network/integration/v1/sites"

    async def _async_update_data(self):
        headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json"
        }

        try:
            async with self.session.get(self.url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    _LOGGER.error("Unauthorized. Check your UniFi API key.")
                    return {"error": "Unauthorized"}
                else:
                    text = await response.text()
                    _LOGGER.error(f"Error fetching data: {response.status} - {text}")
                    return {"error": f"{response.status}: {text}"}
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error: {err}")
            return {"error": str(err)}
