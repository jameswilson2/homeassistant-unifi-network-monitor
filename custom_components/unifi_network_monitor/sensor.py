from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        UniFiStatSensor(coordinator, "client_count"),
        UniFiStatSensor(coordinator, "wan_ip"),
        UniFiStatSensor(coordinator, "cpu_util"),
        UniFiStatSensor(coordinator, "mem_util"),
        UniFiStatSensor(coordinator, "uptime"),
        UniFiStatSensor(coordinator, "firmware_version"),
    ]
    async_add_entities(sensors)

class UniFiStatSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        self._key = key

    @property
    def name(self):
        return f"UniFi {self._key.replace('_', ' ').title()}"

    @property
    def unique_id(self):
        return f"unifi_network_{self._key}"

    @property
    def native_value(self):
        data = self.coordinator.data
        if self._key == "client_count":
            return len(data.get("clients", []))
        elif self._key == "wan_ip":
            return data.get("sysinfo", {}).get("wan_ip")
        elif self._key == "cpu_util":
            return data.get("devices", [{}])[0].get("system-stats", {}).get("cpu")
        elif self._key == "mem_util":
            return data.get("devices", [{}])[0].get("system-stats", {}).get("mem")
        elif self._key == "uptime":
            return data.get("devices", [{}])[0].get("uptime")
        elif self._key == "firmware_version":
            return data.get("devices", [{}])[0].get("version")

    @property
    def available(self):
        return self.coordinator.last_update_success
