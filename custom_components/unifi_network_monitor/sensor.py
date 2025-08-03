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
    "adoptedAt": {"name": "Adopted At", "icon": "mdi:calendar-clock"},
    "provisionedAt": {"name": "Provisioned At", "icon": "mdi:calendar-clock"},
    "configurationId": {"name": "Configuration ID", "icon": "mdi:identifier"},
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    controller = hass.data[DOMAIN][entry.entry_id]
    await controller.update_data()
    entities = []

    # Site name sensor (optional)
    entities.append(UniFiSiteSensor(controller))

    # For each device, create a sensor for each attribute
    for device in controller.devices:
        # Standard device attributes
        for attr, desc in SENSOR_TYPES.items():
            entities.append(
                UniFiDeviceAttributeSensor(device, attr, desc["name"], desc["icon"])
            )

        # Per-port sensors
        interfaces = device.get("interfaces", {})
        if isinstance(interfaces, dict):
            ports = interfaces.get("ports", [])
            for port in ports:
                idx = port.get("idx")
                if idx is None:
                    continue
                # Enabled
                entities.append(
                    UniFiPortSensor(
                        device,
                        port,
                        idx,
                        "enabled",
                        f"Port {idx} Enabled",
                        "mdi:power"
                    )
                )
                # Connector
                entities.append(
                    UniFiPortSensor(
                        device,
                        port,
                        idx,
                        "connector",
                        f"Port {idx} Connector",
                        "mdi:ethernet"
                    )
                )
                # Speed
                entities.append(
                    UniFiPortSensor(
                        device,
                        port,
                        idx,
                        "speedMbps",
                        f"Port {idx} Speed",
                        "mdi:speedometer"
                    )
                )
                # PoE Standard
                poe_standard = port.get("poe", {}).get("standard") if isinstance(port.get("poe"), dict) else None
                if poe_standard is not None:
                    entities.append(
                        UniFiPortSensor(
                            device,
                            port,
                            idx,
                            "poe_standard",
                            f"Port {idx} PoE Standard",
                            "mdi:flash"
                        )
                    )

        # Per-radio sensors
        radios = interfaces.get("radios", []) if isinstance(interfaces, dict) else []
        for i, radio in enumerate(radios):
            # wlanStandard
            if "wlanStandard" in radio:
                entities.append(
                    UniFiRadioSensor(
                        device,
                        radio,
                        i,
                        "wlanStandard",
                        f"Radio {i+1} WLAN Standard",
                        "mdi:wifi"
                    )
                )
            # frequencyGHz
            if "frequencyGHz" in radio:
                entities.append(
                    UniFiRadioSensor(
                        device,
                        radio,
                        i,
                        "frequencyGHz",
                        f"Radio {i+1} Frequency (GHz)",
                        "mdi:wifi"
                    )
                )
            # channelWidthMHz
            if "channelWidthMHz" in radio:
                entities.append(
                    UniFiRadioSensor(
                        device,
                        radio,
                        i,
                        "channelWidthMHz",
                        f"Radio {i+1} Channel Width (MHz)",
                        "mdi:wifi"
                    )
                )
            # channel
            if "channel" in radio:
                entities.append(
                    UniFiRadioSensor(
                        device,
                        radio,
                        i,
                        "channel",
                        f"Radio {i+1} Channel",
                        "mdi:wifi"
                    )
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
        )

    async def async_update(self):
        pass

    @property
    def state(self):
        value = self._device.get(self._attribute)
        # Convert booleans to Yes/No for display
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return value

class UniFiPortSensor(Entity):
    def __init__(self, device, port, idx, attribute, friendly_name, icon):
        self._device = device
        self._port = port
        self._idx = idx
        self._attribute = attribute
        self._attr_name = f"{device.get('name', device.get('macAddress', 'Unknown'))} {friendly_name}"
        self._attr_unique_id = f"unifi_{device.get('macAddress', 'unknown')}_port{idx}_{attribute}"
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers = {(DOMAIN, self._device.get("macAddress"))},
            name = self._device.get("name"),
            model = self._device.get("model"),
            manufacturer = "Ubiquiti",
            sw_version = self._device.get("firmwareVersion"),
        )

    async def async_update(self):
        pass

    @property
    def state(self):
        if self._attribute == "poe_standard":
            poe = self._port.get("poe", {})
            return poe.get("standard") if isinstance(poe, dict) else None
        value = self._port.get(self._attribute)
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return value

class UniFiRadioSensor(Entity):
    def __init__(self, device, radio, idx, attribute, friendly_name, icon):
        self._device = device
        self._radio = radio
        self._idx = idx
        self._attribute = attribute
        self._attr_name = f"{device.get('name', device.get('macAddress', 'Unknown'))} {friendly_name}"
        self._attr_unique_id = f"unifi_{device.get('macAddress', 'unknown')}_radio{idx}_{attribute}"
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers = {(DOMAIN, self._device.get("macAddress"))},
            name = self._device.get("name"),
            model = self._device.get("model"),
            manufacturer = "Ubiquiti",
            sw_version = self._device.get("firmwareVersion"),
        )

    async def async_update(self):
        pass

    @property
    def state(self):
        value = self._radio.get(self._attribute)
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return value
