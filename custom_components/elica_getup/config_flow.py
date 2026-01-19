"""Config flow for Elica Getup integration."""
import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, URL_TOKEN, AUTH_BASIC

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("username", description={"suggested_value": "your.email@example.com"}): str,
    vol.Required("password"): str,
    vol.Required("app_uuid", description={"suggested_value": "af3c7b5d2f17b6da"}): str,
    vol.Required("device_name", default="Elica Getup"): str,
})


async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect.
    
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    username = data["username"]
    password = data["password"]
    app_uuid = data["app_uuid"]

    # Try to authenticate
    auth_data = {
        'scope': 'default',
        'grant_type': 'password',
        'username': username,
        'password': password,
        'app_uuid': app_uuid
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            URL_TOKEN,
            data=auth_data,
            headers={'Authorization': AUTH_BASIC}
        ) as resp:
            if resp.status != 200:
                raise InvalidAuth
            
            result = await resp.json()
            if not result.get("access_token"):
                raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Elica Getup"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elica Getup."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on username to prevent duplicates
                await self.async_set_unique_id(user_input["username"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
