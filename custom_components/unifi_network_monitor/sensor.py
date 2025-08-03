from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    controller = hass.data[DOMAIN][entry.entry_id]
    entities = [UniFiSiteSensor(controller)]
    async_add_entities(entities, True)

class UniFiSiteSensor(Entity):
    def __init__(self, controller):
        self._controller = controller
        self._attr_name = "UniFi Site Name"
        self._attr_unique_id = "unifi_site_name"

    async def async_update(self):
        await self._controller.update_data()

    @property
    def state(self):
        return self._controller.site_name
