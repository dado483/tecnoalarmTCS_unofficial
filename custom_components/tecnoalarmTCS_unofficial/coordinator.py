import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class TecnoalarmDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator per gestire l'aggiornamento dei dati Tecnoalarm."""

    def __init__(self, hass: HomeAssistant, session, centrale_id: str) -> None:
        """Inizializza il coordinatore."""
        super().__init__(
            hass,
            _LOGGER,
            name="TecnoalarmDataUpdateCoordinator",
            update_interval=timedelta(seconds=5),  # Aggiorna ogni 5 secondi
            always_update=True,
        )
        self._session = session
        self._centrale_id = centrale_id
        self.zones = []
        self.programs = {}

    async def _async_setup(self):
        """Setup iniziale: carica la configurazione una sola volta."""
        _LOGGER.debug("Setup iniziale del coordinator Tecnoalarm")
        await self.hass.async_add_executor_job(self._session.get_centrali)
        await self.hass.async_add_executor_job(
            self._session.select_centrale,
            self._session.centrali[self._centrale_id].tp
        )

#        self.zones = self._session.get_zones
#        self.programs = self._session.get_programs
#        self.programs = self._session.centrali[self._centrale_id].tp.status.programs

        try:
            zones, programs = await asyncio.gather(
                self.hass.async_add_executor_job(self._session.get_zones),
                self.hass.async_add_executor_job(self._session.get_programs),
            )
            self.zones = zones
            _LOGGER.debug(f"Zone Iniziali: {self.zones}")
            if programs.root:
                self.programs = {i: p for i, p in enumerate(programs.root)}
                _LOGGER.debug(f"Programs Iniziali: {self.programs}")
        except Exception as err:
            _LOGGER.error(f"Errore nell'aggiornare Tecnoalarm: {err}")
            raise UpdateFailed from err

    async def async_update_all(self):
        """Aggiorna zones e programs da Tecnoalarm."""
        _LOGGER.debug("Aggiorno tutte le informazioni da Tecnoalarm")
        try:
            zones, programs = await asyncio.gather(
                self.hass.async_add_executor_job(self._session.get_zones),
                self.hass.async_add_executor_job(self._session.get_programs),
            )
            self.zones = zones
            _LOGGER.debug(f"Zone Aggiornate: {self.zones}")
            if programs.root:
                self.programs = {i: p for i, p in enumerate(programs.root)}
                _LOGGER.debug(f"Programs Aggiornati: {self.programs}")
            self.last_update = dt_util.now()
            return {
                "zones": self.zones,
                "programs": self.programs,
                "last_update": self.last_update
            }
        except Exception as err:
            _LOGGER.error(f"Errore nell'aggiornare Tecnoalarm: {err}")
            raise UpdateFailed from err

    async def _async_update_data(self):
        """Metodo chiamato dal sistema Home Assistant per aggiornare i dati."""
        return await self.async_update_all()
