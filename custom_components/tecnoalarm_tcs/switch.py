from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN
from pytcs_tecnoalarm.api_models import TcsTpstatusObjectZones
from . import disable_program, enable_program
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Imposta il sensore per ogni programma."""
    _LOGGER.debug("Setting up Programs Switch")
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    programs = hass.data[DOMAIN][entry.entry_id]["session"].centrali[hass.data[DOMAIN][entry.entry_id]["centrale"]].tp.status.programs
    for idx, obj in enumerate(programs):
        async_add_entities([TCSprogram(coordinator, idx, obj, entry)])
        async_add_entities([AwayTCSprogram(obj)])
        async_add_entities([NightTCSprogram(obj)])

class AwayTCSprogram(SwitchEntity, RestoreEntity):
    def __init__(self, obj:TcsTpstatusObjectZones):
        self._obj = obj
        self._attr_is_on = False

    @property
    def name(self):
        return f"config_away_{self._obj.description.lower()}"

    @property
    def unique_id(self):
        return f"config_away_{self._obj.description.lower()}"

    async def async_added_to_hass(self):
        """Ripristina stato precedente se disponibile."""
        state = await self.async_get_last_state()
        if state and state.state == "on":
            self._attr_is_on = True
        else:
            self._attr_is_on = False

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self._attr_is_on

    @property
    def icon(self):
        return "mdi:shield-check-outline" if self.is_on else "mdi:shield-off-outline"

class NightTCSprogram(SwitchEntity, RestoreEntity):
    def __init__(self, obj:TcsTpstatusObjectZones):
        self._obj = obj
        self._attr_is_on = False

    @property
    def name(self):
        return f"config_night_{self._obj.description.lower()}"

    @property
    def unique_id(self):
        return f"config_night_{self._obj.description.lower()}"

    async def async_added_to_hass(self):
        """Ripristina stato precedente se disponibile."""
        state = await self.async_get_last_state()
        if state and state.state == "on":
            self._attr_is_on = True
        else:
            self._attr_is_on = False

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self._attr_is_on

    @property
    def icon(self):
        return "mdi:shield-check-outline" if self.is_on else "mdi:shield-off-outline"

class TCSprogram(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, program_id: int, obj:TcsTpstatusObjectZones, entry):
        super().__init__(coordinator)
        self._program_id = program_id
        self._name = obj.description.lower()
        self.obj = obj
        self._zones = obj.zones
        self._entry = entry
        _LOGGER.debug(f"Program {self._name} has {len(self._zones)} zones")

    @property
    def name(self):
        return f"program_{self._program_id}_{self._name}"

    @property
    def unique_id(self):
        return f"program_{self._program_id}_{self._name}"

    async def async_turn_on(self, **kwargs):
        if self.all_closed:
            _LOGGER.warning(f"Tutto chiuso per il programma {self._name}, posso procedere con l'attivazione")
            if await enable_program(self.coordinator, self._program_id):
                _LOGGER.warning(f"Enabled program {self._name} (id={self._program_id})")
                await self.coordinator.async_request_refresh()
        else:
            _LOGGER.debug("Zone Aperte!!")

    async def async_turn_off(self, **kwargs):
        if await disable_program(self.coordinator, self._program_id):
            _LOGGER.warning(f"Disabled program {self._name} (id={self._program_id})")
            await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        """Restituisce lo stato attuale del programma. True se Attivo ovvero stato 2 o 3"""
        program = self.coordinator.data["programs"].get(self._program_id)
        if program is None:
            _LOGGER.error(f"Program {self._program_id} not found in coordinator data.")
            return False
        return program.status in (2, 3)

    @property
    def all_closed(self):
        """Controlla che tutte le zone siano chiuse."""
        zones_status = self.coordinator.data["zones"]
        zones_dict = {zone.idx: zone for zone in zones_status.root}
        _all_closed = all(zones_dict.get(zoneID) and zones_dict[zoneID].status == "CLOSED" for zoneID in self._zones)
        return _all_closed

    @property
    def extra_state_attributes(self):
        """Aggiungi attributi extra."""
        return {
            "all_closed": self.all_closed,
            "last_update": self.coordinator.data["last_update"].isoformat()
        }

