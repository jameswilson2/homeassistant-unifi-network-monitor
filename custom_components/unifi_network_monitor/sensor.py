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
        # Example: show device state (ONLINE, OFFLINE, etc.)
        return self._device.get("state", "unknown")

    @property
    def extra_state_attributes(self):
        # Safely extract nested fields
        uplink = self._device.get("uplink", {})
        features = self._device.get("features", {})
        interfaces = self._device.get("interfaces", {})
        ports = interfaces.get("ports", [])
        radios = interfaces.get("radios", [])

        return {
            "id": self._device.get("id"),
            "name": self._device.get("name"),
            "model": self._device.get("model"),
            "supported": self._device.get("supported"),
            "macAddress": self._device.get("macAddress"),
            "ipAddress": self._device.get("ipAddress"),
            "state": self._device.get("state"),
            "firmwareVersion": self._device.get("firmwareVersion"),
            "firmwareUpdatable": self._device.get("firmwareUpdatable"),
            "adoptedAt": self._device.get("adoptedAt"),
            "provisionedAt": self._device.get("provisionedAt"),
            "configurationId": self._device.get("configurationId"),
            "uplink_deviceId": uplink.get("deviceId"),
            "features_switching": features.get("switching"),
            "features_accessPoint": features.get("accessPoint"),
            "ports": ports,
            "radios": radios,
        }
