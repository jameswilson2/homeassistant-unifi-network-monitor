import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class UniFiController:
    def __init__(self, host: str, api_key: str):
        self._host = host.replace("https://", "").replace("http://", "")
        self._api_key = api_key
        self.site_name = None
        self.site_internal_id = None
        self.devices = []

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
                        self.site_internal_id = data_list[0]["id"] if data_list else "Unknown"
                    else:
                        self.site_name = f"HTTP Error: {resp.status}"
                        _LOGGER.error("UniFi API returned HTTP %d", resp.status)
                        self.devices = []
                        return
        except Exception as e:
            self.site_name = f"Connection Error: {str(e)}"
            _LOGGER.error("Exception fetching UniFi data: %s", e)
            self.devices = []
            return

        if not self.site_name or self.site_name.startswith("HTTP Error") or self.site_name.startswith("Connection Error"):
            self.devices = []
            return

        devices_url = f"https://{self._host}/proxy/network/integration/v1/sites/{self.site_internal_id}/devices"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(devices_url, headers=headers, ssl=False) as resp:
                    if resp.status == 200:
                        devices_data = await resp.json()
                        device_list = devices_data.get("data", [])
                        detailed_devices = []
                        # Fetch details for each device
                        for device in device_list:
                            device_id = device.get("id")
                            if not device_id:
                                continue
                            detail_url = f"https://{self._host}/proxy/network/integration/v1/sites/{self.site_internal_id}/devices/{device_id}"
                            async with session.get(detail_url, headers=headers, ssl=False) as detail_resp:
                                if detail_resp.status == 200:
                                    detail_data = await detail_resp.json()
                                    # Merge the summary and detail data
                                    device.update(detail_data.get("data", {}))
                                else:
                                    _LOGGER.warning("Failed to fetch details for device %s: HTTP %d", device_id, detail_resp.status)
                            detailed_devices.append(device)
                        self.devices = detailed_devices
                        _LOGGER.debug("Fetched %d devices with details", len(self.devices))
                    else:
                        _LOGGER.error("Failed to fetch devices: HTTP %d", resp.status)
                        _LOGGER.debug("Response text: %s", await resp.text())
                        self.devices = []
        except Exception as e:
            _LOGGER.error("Exception fetching UniFi devices: %s", e)
            self.devices = []
