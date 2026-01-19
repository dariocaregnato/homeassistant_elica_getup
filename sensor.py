from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elica Getup sensors from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    devices = entry_data.get("devices", [])
    entities = []
    for device in devices:
        entities.append(ElicaFilterSensor(hass, device, entry.entry_id, "filter_grease"))
        entities.append(ElicaFilterSensor(hass, device, entry.entry_id, "filter_charcoal"))
    async_add_entities(entities, True)

class ElicaFilterSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hass, device, entry_id, dp_id):
        self.hass = hass
        self._entry_id = entry_id
        self._device_id = device["id"]
        self._dp_id = dp_id
        self._attr_translation_key = "filter_carbon" if dp_id == "filter_charcoal" else "filter_grease"
        self._attr_unique_id = f"{self._device_id}_{dp_id}"
        self._attr_native_unit_of_measurement = "%"

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
    def native_value(self):
        for d in self.hass.data[DOMAIN][self._entry_id]["devices"]:
            if d["id"] == self._device_id: return d.get(self._dp_id, 0)
        return 0