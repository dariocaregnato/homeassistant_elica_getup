import aiohttp
import asyncio
import logging
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, URL_DEVICES

_LOGGER = logging.getLogger(__name__)

SPEED_TO_CAPS = {"1": {"64": 1, "110": 1}, "2": {"64": 1, "110": 2}, "3": {"64": 1, "110": 3}, "Boost 1": {"64": 4}, "Boost 2": {"64": 8}}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elica Getup fan from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    devices = entry_data.get("devices", [])
    async_add_entities([ElicaFan(hass, device, entry.entry_id) for device in devices], True)

class ElicaFan(FanEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "fan"

    def __init__(self, hass, device, entry_id):
        self.hass = hass
        self._entry_id = entry_id
        self._device_id = device["id"]
        self._attr_unique_id = f"{self._device_id}_fan"
        self._attr_supported_features = FanEntityFeature.PRESET_MODE | FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON
        self._attr_preset_modes = list(SPEED_TO_CAPS.keys())
        self._app_uuid = hass.data[DOMAIN][entry_id]["app_uuid"]

    @property
    def device_info(self):
        device_name = self.hass.data[DOMAIN][self._entry_id].get("device_name", "Elica Getup")
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": device_name,
            "manufacturer": "Elica",
            "model": "GetUp"
        }

    @property
    def is_on(self):
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: return int(d.get("110", 0)) > 0 or int(d.get("64", 0)) > 1
        return False

    @property
    def preset_mode(self):
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id:
                m64, m110 = int(d.get("64", 0)), int(d.get("110", 0))
                if m64 == 8: return "Boost 2"
                if m64 == 4: return "Boost 1"
                if m64 == 1 and m110 in [1,2,3]: return str(m110)
        return None

    async def _check_and_raise(self):
        pos = 1
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: pos = int(d.get("53", 1))
        if pos != 1:
            await self._send_capabilities({"53": 1})
            for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
                if d["id"] == self._device_id: d["53"] = 1
            self.async_write_ha_state()
            await asyncio.sleep(28)

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs):
        await self._check_and_raise()
        await self.async_set_preset_mode(preset_mode or "1")

    async def async_turn_off(self, **kwargs):
        await self._send_capabilities({"110": 0})
        self._update_local_state({"110": 0})

    async def async_set_preset_mode(self, preset_mode: str):
        await self._check_and_raise()
        caps = SPEED_TO_CAPS.get(preset_mode)
        if caps:
            await self._send_capabilities(caps)
            self._update_local_state(caps)

    def _update_local_state(self, caps):
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: d.update(caps)
        self.async_write_ha_state()

    async def _send_capabilities(self, cap_dict):
        token = self.hass.data[DOMAIN][self._entry_id].get("token")
        payload = {"type": "Hood", "name": "capabilities", "async": True, "capabilities": cap_dict}
        headers = {'Authorization': f'Bearer {token}', 'App-Uuid': self._app_uuid, 'Content-Type': 'application/json'}
        async with aiohttp.ClientSession() as session:
            await session.post(f"{URL_DEVICES}/{self._device_id}/commands", json=payload, headers=headers)