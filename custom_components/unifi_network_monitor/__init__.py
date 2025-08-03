import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .unifi_api import UniFiController

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    controller = UniFiController(entry.data["host"], entry.data["api_key"])
    await controller.update_data()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller

    # Forward setup for sensors platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

