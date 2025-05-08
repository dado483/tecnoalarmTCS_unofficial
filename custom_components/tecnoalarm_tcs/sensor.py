from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from pytcs_tecnoalarm.api_models import TcsTpstatusObjectZones
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Imposta il sensore per ogni programma."""
    _LOGGER.debug("Setting up Programs Status Sensors")
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    programs = hass.data[DOMAIN][entry.entry_id]["session"].centrali[hass.data[DOMAIN][entry.entry_id]["centrale"]].tp.status.programs
    async_add_entities([TCSProgramStatusSensor(coordinator, idx, obj, entry) for idx, obj in enumerate(programs)])

class TCSProgramStatusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, program_id: int, obj:TcsTpstatusObjectZones, entry):
        super().__init__(coordinator)
        self._program_id = program_id
        self._name = obj.description.lower()

    @property
    def obj(self):
        return self.coordinator.data["programs"].get(self._program_id)

    @property
    def name(self):
        return f"sensor_{self._program_id}_{self._name}"

    @property
    def unique_id(self):
        return f"sensor_{self._program_id}_{self._name}"

    @property
    def state(self):
        """Restituisce lo stato del programma in base ai valori di status, alarm e prealarm."""
        program_data = self.obj
        _LOGGER.debug(f"Sensor State: {self._program_id} - {program_data}")
        if program_data is not None:
            status = program_data.status if program_data.status else None
            alarm = program_data.alarm if program_data else False
            prealarm = program_data.prealarm if program_data else False

            if status == 3:  # Program is active
                if alarm:
                    return "Allarme"
                elif prealarm:
                    return "Pre-Allarme"
                else:
                    return "Attivo"
            elif status == 2:  # Program in activation
                return "Attivazione in corso"
            elif status == 1:  # Program in deactivation
                return "Disattivazione in corso"
            else:
                return "Inattivo"  # Program inactive
        else:
            return "Inattivo" # Se program è None ritorno Inattivo

    @property
    def icon(self):
        program_data = self.obj
        if program_data is not None:
            status = program_data.status if program_data.status else None
            alarm = program_data.alarm if program_data else False
            prealarm = program_data.prealarm if program_data else False

            if status == 3:  # Program is active
                if alarm:
                    return "mdi:shield-alert"
                elif prealarm:
                    return "mdi:shield-alert"
                else:
                    return "mdi:shield-home"
            elif status == 2:  # Program in activation
                return "mdi:shield-half-full"
            elif status == 1:  # Program in deactivation
                return "mdi:shield-off"
            else:
                return "mdi:shield-off"  # Program inactive
        else:
            return "mdi:shield-off" # Se program è None ritorno Inattivo

    @property
    def extra_state_attributes(self):
        """Aggiungi dettagli extra sul programma."""
        return {
            "last_update": self.coordinator.data["last_update"].isoformat()
        }
