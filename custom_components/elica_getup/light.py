import aiohttp
import asyncio
import logging
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, URL_DEVICES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elica Getup light from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    devices = entry_data.get("devices", [])
    async_add_entities([ElicaLight(hass, device, entry.entry_id) for device in devices], True)

class ElicaLight(LightEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "light"

    def __init__(self, hass, device, entry_id):
        self.hass = hass
        self._entry_id = entry_id
        self._device_id = device["id"]
        self._attr_unique_id = f"{self._device_id}_light"
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._app_uuid = hass.data[DOMAIN][entry_id]["app_uuid"]

    @property
    def device_info(self):
        device_name = self.hass.data[DOMAIN][self._entry_id].get("device_name", "Elica Getup")
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": device_name,
            "manufacturer": "Elica",
            "model": "GetUp",
        }

    @property
    def is_on(self):
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: return float(d.get("96", 0)) > 0
        return False

    @property
    def brightness(self):
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: return int(float(d.get("96", 0)) * 2.55)
        return 0

    async def async_turn_on(self, **kwargs):
        pos = 1
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: pos = int(d.get("53", 1))
        
        if pos != 1:
            await self._send_capabilities({"53": 1})
            self._update_local_state({"53": 1})
            await asyncio.sleep(28)

        brightness = kwargs.get("brightness", self.brightness if self.brightness > 0 else 255)
        level = int(brightness / 2.55)
        await self._send_capabilities({"96": level, "71": 1})
        self._update_local_state({"96": level, "71": 1})

    async def async_turn_off(self, **kwargs):
        await self._send_capabilities({"96": 0})
        self._update_local_state({"96": 0})

    def _update_local_state(self, caps):
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: d.update(caps)
        self.async_write_ha_state()

    async def _send_capabilities(self, cap_dict):
        token = self.hass.data[DOMAIN][self._entry_id].get("token")
        payload = {"type": "Hood", "name": "capabilities", "async": True, "capabilities": cap_dict}
        headers = {'Authorization': f'Bearer {token}', 'App-Uuid': self._app_uuid}
        async with aiohttp.ClientSession() as session:
            await session.post(f"{URL_DEVICES}/{self._device_id}/commands", json=payload, headers=headers)