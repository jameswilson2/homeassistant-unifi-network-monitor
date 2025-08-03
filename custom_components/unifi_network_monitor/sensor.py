from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

SENSOR_TYPES = {
    "ipAddress": {"name": "IP Address", "icon": "mdi:ip-network"},
    "firmwareVersion": {"name": "Firmware Version", "icon": "mdi:chip"},
    "state": {"name": "State", "icon": "mdi:lan-connect"},
    "model": {"name": "Model", "icon": "mdi:access-point"},
    "supported": {"name": "Supported", "icon": "mdi:check-circle"},
    "firmwareUpdatable": {"name": "Firmware Updatable", "icon": "mdi:update"},
    # Add more attributes here as needed
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    controller = hass.data[DOMAIN][entry.entry_id]
    await controller.update_data()
    entities = []

    # Site name sensor (optional)
    entities.append(UniFiSiteSensor(controller))

    # For each device, create a sensor for each attribute
    for device in controller.devices:
        for attr, desc in SENSOR_TYPES.items():
            entities.append(
                UniFiDeviceAttributeSensor(device, attr, desc["name"], desc["icon"])
            )

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

class UniFiDeviceAttributeSensor(Entity):
    def __init__(self, device, attribute, friendly_name, icon):
        self._device = device
        self._attribute = attribute
        self._attr_name = f"{device.get('name', device.get('macAddress', 'Unknown'))} {friendly_name}"
        self._attr_unique_id = f"unifi_{device.get('macAddress', 'unknown')}_{attribute}"
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers = {(DOMAIN, self._device.get("macAddress"))},
            name = self._device.get("name"),
            model = self._device.get("model"),
            manufacturer = "Ubiquiti",
            sw_version = self._device.get("firmwareVersion"),
            configuration_url = None,
        )

    async def async_update(self):
        # No-op: device data is refreshed by controller
        pass

    @property
    def state(self):
        return self._device.get(self._attribute)
