import logging
import httpx
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class UniFiClient:
    def __init__(self, host, port, site, api_key, verify_ssl):
        self._base_url = f"https://{host}:{port}/proxy/network/api/s/{site}"
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._verify = verify_ssl

    async def get_stats(self):
        async with httpx.AsyncClient(verify=self._verify) as client:
            try:
                responses = await asyncio.gather(
                    client.get(f"{self._base_url}/stat/device", headers=self._headers),
                    client.get(f"{self._base_url}/stat/health", headers=self._headers),
                    client.get(f"{self._base_url}/stat/clients", headers=self._headers),
                    client.get(f"{self._base_url}/stat/sysinfo", headers=self._headers),
                    client.get(f"{self._base_url}/rest/networkconf", headers=self._headers),
                )

                data = {
                    "devices": responses[0].json().get("data", []),
                    "health": responses[1].json().get("data", []),
                    "clients": responses[2].json().get("data", []),
                    "sysinfo": responses[3].json().get("data", {}),
                    "vlans": responses[4].json().get("data", []),
                }
                return data
            except Exception as e:
                raise UpdateFailed(f"Error fetching UniFi data: {e}")

class UniFiDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config):
        self.client = UniFiClient(
            config["host"],
            config["port"],
            config["site"],
            config["api_key"],
            config["verify_ssl"],
        )
        super().__init__(
            hass,
            _LOGGER,
            name="UniFi Network Monitor",
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        return await self.client.get_stats()
