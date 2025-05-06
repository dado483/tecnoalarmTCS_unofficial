
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pytcs_tecnoalarm.api_models import TcsZoneObj, ZoneStatusEnum
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Imposta il sensore per ogni programma."""
    _LOGGER.debug("Setting up Binary Sensors")
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    for zone in coordinator.zones.root:
        if zone.allocated:
            _LOGGER.debug(f"adding #{zone.idx} {zone.description}")
            async_add_entities([AlarmSensor(coordinator,zone,entry)])
            async_add_entities([AlarmSensorBattery(coordinator,zone,entry)])
    async_add_entities([ConfigAwayStatus(coordinator)])
    async_add_entities([ConfigNightStatus(coordinator)])
    async_add_entities([ConfigUndefinedStatus(coordinator)])

class ConfigAwayStatus(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def name(self):
        return "config_away_status"

    @property
    def unique_id(self):
        return "config_away_status"

    @property
    def is_on(self) -> bool:
        has_active_sensors = False
        program_match = True
        programs = self.coordinator._session.centrali[self.coordinator._centrale_id].tp.status.programs
        for idx, obj in enumerate(programs):
            away_switch = self.coordinator.hass.states.get(f"switch.config_away_{obj.description.lower()}")
            away_on = away_switch.state == 'on' if away_switch else False
            sensor_state = self.coordinator.hass.states.get(f"sensor.sensor_{idx}_{obj.description.lower()}").state
            if sensor_state != "Inattivo":
                has_active_sensors = True
                if not away_on:
                    program_match = False
            else:
                if away_on:
                    program_match = False
        return has_active_sensors and program_match

    @property
    def icon(self):
        return "mdi:shield-airplane" if self.is_on else "mdi:shield-airplane-outline"

class ConfigNightStatus(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def name(self):
        return "config_night_status"

    @property
    def unique_id(self):
        return "config_night_status"

    @property
    def is_on(self) -> bool:
        has_active_sensors = False
        program_match = True
        programs = self.coordinator._session.centrali[self.coordinator._centrale_id].tp.status.programs
        for idx, obj in enumerate(programs):
            night_switch = self.coordinator.hass.states.get(f"switch.config_night_{obj.description.lower()}")
            night_on = night_switch.state == 'on' if night_switch else False
            sensor_state = self.coordinator.hass.states.get(f"sensor.sensor_{idx}_{obj.description.lower()}").state
            if sensor_state != "Inattivo":
                has_active_sensors = True
                if not night_on:
                    program_match = False
            else:
                if night_on:
                    program_match = False
        return has_active_sensors and program_match

    @property
    def icon(self):
        return "mdi:shield-moon" if self.is_on else "mdi:shield-moon-outline"

class ConfigUndefinedStatus(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

    @property
    def name(self):
        return "config_undefined_status"

    @property
    def unique_id(self):
        return "config_undefined_status"

    @property
    def is_on(self) -> bool:
        has_active_sensors = False
        program_match = True
        programs = self.coordinator._session.centrali[self.coordinator._centrale_id].tp.status.programs
        away_switch_status = self.coordinator.hass.states.get("binary_sensor.config_away_status")
        away_status_on = away_switch_status.state == 'on' if away_switch_status else False
        night_switch_status = self.coordinator.hass.states.get("binary_sensor.config_night_status")
        night_status_on = night_switch_status.state == 'on' if night_switch_status else False
        for idx, obj in enumerate(programs):
            sensor_state = self.coordinator.hass.states.get(f"sensor.sensor_{idx}_{obj.description.lower()}").state
            if sensor_state != "Inattivo":
                has_active_sensors = True
            if (away_status_on or night_status_on):
                program_match = False
        return has_active_sensors and program_match

    @property
    def icon(self):
        return "mdi:shield-alert" if self.is_on else "mdi:shield-alert-outline"

class AlarmSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, obj:TcsZoneObj, entry):
        super().__init__(coordinator)
        self._name = obj.description.lower()
        self._sensor_id = obj.idx
        self._entry = entry
        self.obj = obj
        self._attr_device_class = BinarySensorDeviceClass.WINDOW

    @property
    def name(self):
        return f"zone_{self._entry.title.lower()}_{self._sensor_id}_{self._name}"

    @property
    def unique_id(self):
        return f"zone_{self._entry.title.lower()}_{self._sensor_id}_{self._name}"

    @property
    def is_on(self):
        zones_list = self.coordinator.data["zones"].root
        try:
            sensor = zones_list[self._sensor_id]
            return sensor.status == ZoneStatusEnum.OPEN
        except IndexError:
            return False

class AlarmSensorBattery(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, obj:TcsZoneObj, entry):
        super().__init__(coordinator)
        self._name = obj.description.lower()
        self._sensor_id = obj.idx
        self._entry = entry
        self.obj = obj
        self._attr_device_class = BinarySensorDeviceClass.BATTERY

    @property
    def name(self):
        return f"battery_{self._entry.title.lower()}_{self._sensor_id}_{self._name}"

    @property
    def unique_id(self):
        return f"battery_{self._entry.title.lower()}_{self._sensor_id}_{self._name}"

    @property
    def is_on(self):
        zones_list = self.coordinator.data["zones"].root
        try:
            sensor = zones_list[self._sensor_id]
            return sensor.inLowBattery is True
        except IndexError:
            return False
