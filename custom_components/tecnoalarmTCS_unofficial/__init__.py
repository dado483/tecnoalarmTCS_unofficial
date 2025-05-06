import logging
import pytcs_tecnoalarm
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from pytcs_tecnoalarm import TCSSession
from pytcs_tecnoalarm.api_models import TcsTpstatusObjectZones

from .coordinator import TecnoalarmDataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up myTecnoalarm_Unofficial component from a config entry."""
    _LOGGER.info("Setting up myTecnoalarm_Unofficial integration")

    session = await hass.async_add_executor_job(
        TCSSession,
        config.data["token"],
        config.data["appid"]
    )

    coordinator = TecnoalarmDataUpdateCoordinator(hass, session, config.data["centrale"])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[config.entry_id] = {
        "session": session,
        "coordinator": coordinator,
        "centrale": config.data["centrale"]
    }

    # Forward setup to binary sensors, switches, and sensors
    await hass.config_entries.async_forward_entry_setups(config, ["switch", "sensor", "binary_sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch", "sensor", "binary_sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def disable_program(coordinator, prg_id: int):
    _LOGGER.info(f"Disabling program {prg_id}")
    try:
        await coordinator.hass.async_add_executor_job(coordinator._session.disable_program,prg_id)
        return True
    except Exception as e:
        _LOGGER.error(f"Failed to disable program: {e}")
        return False

async def enable_program(coordinator, prg_id: int):
    _LOGGER.info(f"Enabling program {prg_id}")
    try:
        await coordinator.hass.async_add_executor_job(coordinator._session.enable_program,prg_id)
        return True
    except Exception as e:
        _LOGGER.error(f"Failed to enable program: {e}")
        return False
