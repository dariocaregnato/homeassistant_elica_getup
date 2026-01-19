import aiohttp
import asyncio
import logging
from homeassistant.components.cover import CoverEntity, CoverEntityFeature, CoverDeviceClass
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
    """Set up Elica Getup cover from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    devices = entry_data.get("devices", [])
    async_add_entities([ElicaCover(hass, device, entry.entry_id) for device in devices], True)

class ElicaCover(CoverEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "position"

    def __init__(self, hass, device, entry_id):
        self.hass = hass
        self._entry_id = entry_id
        self._device_id = device["id"]
        self._attr_unique_id = f"{self._device_id}_cover"
        self._attr_device_class = CoverDeviceClass.DAMPER
        self._attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        self._app_uuid = hass.data[DOMAIN][entry_id]["app_uuid"]
        self._is_moving_to = None

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
    def is_opening(self): return self._is_moving_to == "open"
    @property
    def is_closing(self): return self._is_moving_to == "closed"

    @property
    def is_closed(self):
        if self._is_moving_to == "closed": return False
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: return int(d.get("53", 1)) != 1
        return False

    async def async_open_cover(self, **kwargs):
        self._is_moving_to = "open"
        self.async_write_ha_state()
        await self._send_capabilities({"53": 1})
        await asyncio.sleep(28)
        self._is_moving_to = None
        self._update_local_state({"53": 1})

    async def async_close_cover(self, **kwargs):
        self._is_moving_to = "closed"
        self.async_write_ha_state()
        await self._send_capabilities({"96": 0, "110": 0})
        await asyncio.sleep(1.5)
        await self._send_capabilities({"53": 0})
        await asyncio.sleep(28)
        self._is_moving_to = None
        self._update_local_state({"53": 4, "96": 0, "110": 0})

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