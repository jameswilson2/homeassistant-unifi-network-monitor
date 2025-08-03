from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    controller = hass.data[DOMAIN][entry.entry_id]
    await controller.update_data()
    entities = []

    # Site name sensor (optional, keep if you want)
    entities.append(UniFiSiteSensor(controller))

    # Add a sensor for each device
    for device in controller.devices:
        entities.append(UniFiDeviceSensor(device))

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

class UniFiDeviceSensor(Entity):
    def __init__(self, device):
        self._device = device
        self._attr_name = f"UniFi Device {device.get('name', device.get('macAddress', 'Unknown'))}"
        self._attr_unique_id = f"unifi_device_{device.get('macAddress', 'unknown')}"

    async def async_update(self):
        # No-op: device data is refreshed by controller
        pass

    @property
    def state(self):
        # Example: show device state (1=connected, 0=disconnected)
        return self._device.get("state", "unknown")

    @property
    def extra_state_attributes(self):
        # Expose more device info as attributes
        return {
            "model": self._device.get("model"),
            "ipAddress": self._device.get("ipAddress"),
            "version": self._device.get("version"),
            "last_seen": self._device.get("last_seen"),
            "type": self._device.get("type"),
            "macAddress": self._device.get("macAddress"),
        }
