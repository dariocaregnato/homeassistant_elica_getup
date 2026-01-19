"""The Elica Getup integration."""
import logging
import aiohttp
import asyncio
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.const import Platform

from .const import DOMAIN, URL_TOKEN, URL_DEVICES, AUTH_BASIC

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.FAN, Platform.SENSOR, Platform.COVER]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Elica Getup component from yaml configuration."""
    # This is kept for backward compatibility but does nothing
    # Users should migrate to config flow
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elica Getup from a config entry."""
    username = entry.data["username"]
    password = entry.data["password"]
    app_uuid = entry.data["app_uuid"]
    device_name = entry.data.get("device_name", "Elica Getup")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "token": None,
        "devices": [],
        "app_uuid": app_uuid,
        "username": username,
        "password": password,
        "device_name": device_name,
    }

    async def update_elica_data(now=None):
        """Update data from Elica cloud."""
        entry_data = hass.data[DOMAIN][entry.entry_id]
        
        async with aiohttp.ClientSession() as session:
            # Get token if we don't have one
            if entry_data["token"] is None:
                auth = {
                    'scope': 'default',
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                    'app_uuid': app_uuid
                }
                try:
                    async with session.post(
                        URL_TOKEN,
                        data=auth,
                        headers={'Authorization': AUTH_BASIC}
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            entry_data["token"] = result.get("access_token")
                        else:
                            _LOGGER.error("Failed to get token: %s", resp.status)
                            return
                except Exception as err:
                    _LOGGER.error("Error getting token: %s", err)
                    return

            # Get devices
            headers = {
                'Authorization': f'Bearer {entry_data["token"]}',
                'App-Uuid': app_uuid
            }
            try:
                async with session.get(URL_DEVICES, headers=headers) as resp:
                    if resp.status == 200:
                        devices = await resp.json()
                        if not isinstance(devices, list):
                            devices = [devices]
                        
                        # Process devices
                        processed = []
                        for device in devices:
                            dm = device.get("dataModel", {})
                            for key in ["64", "71", "96", "110", "53"]:
                                if key in dm:
                                    device[key] = int(dm[key])
                            
                            # Process filters
                            for f in device.get("filters", []):
                                if f.get("type") == "charcoal":
                                    device["filter_charcoal"] = f.get("efficiency", 0)
                                elif f.get("type") == "grease":
                                    device["filter_grease"] = f.get("efficiency", 0)
                            
                            processed.append(device)
                        
                        entry_data["devices"] = processed
                    elif resp.status == 401:
                        # Token expired, reset it
                        entry_data["token"] = None
                        _LOGGER.warning("Token expired, will refresh on next update")
                    else:
                        _LOGGER.error("Failed to get devices: %s", resp.status)
            except Exception as err:
                _LOGGER.error("Error getting devices: %s", err)

    # Initial data fetch
    await update_elica_data()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Schedule periodic updates
    entry.async_on_unload(
        async_track_time_interval(hass, update_elica_data, timedelta(seconds=60))
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok