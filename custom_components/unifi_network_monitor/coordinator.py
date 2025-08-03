# custom_components/unifi_network_monitor/coordinator.py

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
import logging
import aiohttp
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=10)

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
        self.base_url = config_data["base_url"].rstrip("/")
        self.sites_url = self.base_url + "/proxy/network/integration/v1/sites"
        self.devices_url_template = self.base_url + "/proxy/network/integration/v1/sites/{site_id}/devices"

    async def _async_update_data(self):
        headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json"
        }

        data = {}
        # Fetch sites
        try:
            async with self.session.get(self.sites_url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    sites_json = await response.json()
                    data["sites"] = sites_json.get("data", [])
                elif response.status == 401:
                    _LOGGER.error("Unauthorized. Check your UniFi API key.")
                    data["error"] = "Unauthorized"
                    return data
                else:
                    text = await response.text()
                    _LOGGER.error(f"Error fetching sites: {response.status} - {text}")
                    data["error"] = f"{response.status}: {text}"
                    return data
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error fetching sites: {err}")
            data["error"] = str(err)
            return data

        # Fetch devices for each site
        data["devices"] = []
        for site in data.get("sites", []):
            site_id = site.get("id")
            if not site_id:
                continue
            devices_url = self.devices_url_template.format(site_id=site_id)
            try:
                async with self.session.get(devices_url, headers=headers, ssl=False) as dev_response:
                    if dev_response.status == 200:
                        devices_json = await dev_response.json()
                        # Attach site_id to each device for context if needed
                        for device in devices_json.get("data", []):
                            device["site_id"] = site_id
                            data["devices"].append(device)
                    else:
                        text = await dev_response.text()
                        _LOGGER.error(f"Error fetching devices for site {site_id}: {dev_response.status} - {text}")
            except aiohttp.ClientError as err:
                _LOGGER.error(f"Network error fetching devices for site {site_id}: {err}")

        return data
