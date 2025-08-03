import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class UniFiController:
    def __init__(self, host: str, api_key: str):
        # Sanitize host to avoid bad URLs
        self._host = host.replace("https://", "").replace("http://", "")
        self._api_key = api_key
        self.site_name = None

    async def update_data(self):
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
        except Exception as e:
            self.site_name = f"Connection Error: {str(e)}"
            _LOGGER.error("Exception fetching UniFi data: %s", e)
