from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class UniFiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="UniFi Network Monitor", data=user_input)

        data_schema = vol.Schema({
            vol.Required("host"): str,
            vol.Required("api_key"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
