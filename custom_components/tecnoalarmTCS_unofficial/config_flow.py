from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import callback
from pytcs_tecnoalarm import TCSSession
from pytcs_tecnoalarm.exceptions import OTPException

from typing import Any
from .const import (
    DOMAIN
)

import voluptuous as vol
import logging


#class OTPException(ValueError): ...

_LOGGER = logging.getLogger(__name__)

VOL_SCHEMA_HOMECONFIG = vol.Schema(
    {
        vol.Required("homeName", description={"suggested_value": "Casa"}): str,
        vol.Required("email", description={"suggested_value": "my-email@gmail.com"}): str,
        vol.Required("password"): str,
    }
)

VOL_SCHEMA_HOMECONFIG_OTP = vol.Schema(
    {
        vol.Required("OTP"): str
    }
)



@callback
def configured_instances(hass):
    return [
        entry.entry_id for entry in hass.config_entries.async_entries(DOMAIN)
    ]

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None)-> ConfigFlowResult:
        _LOGGER.info("Start Config Flow")
        errors = {}

        if user_input is not None:
            _LOGGER.debug(user_input)
            myTCSSession = TCSSession()
            try:
                self.user_data = user_input
                self.myTCSSession = myTCSSession
                await self.hass.async_add_executor_job(myTCSSession.login, user_input["email"], user_input["password"])
                #await myTCSSession.login(user_input["email"], user_input["password"])
                _LOGGER.debug("done")

                return self.async_create_entry(title=user_input["homeName"],
                                               data={
                                                   "token": self.myTCSSession.token,
                                                    "appid": self.myTCSSession.appid
                                                    })
            except OTPException:
                return await self.async_step_otp()  # Passa alla richiesta di OTP
            except ValueError as e:
                _LOGGER.debug(f"Cannot login: {type(e).__name__}")
                errors["base"] = "cannot_login"

            except Exception as e:
                _LOGGER.debug(f"General Error: {e}")
                errors["base"] = "general_error"

        return self.async_show_form(step_id="user",
                                    data_schema=VOL_SCHEMA_HOMECONFIG,
                                    errors=errors)

    async def async_step_otp(self, user_input=None):
        """Secondo step: richiedi OTP."""
        errors = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(self.myTCSSession.login, self.user_data["email"], self.user_data["password"],user_input["OTP"])
                _LOGGER.debug("Connected!!")

                return await self.async_step_centrale()  # Passa alla richiesta della centrale

            except ValueError as e:
                _LOGGER.debug(f"Cannot login: {type(e).__name__}")
                errors["base"] = "cannot_login"

            except Exception as e:
                _LOGGER.debug(f"General Error: {e}")
                errors["base"] = "general_error"

        return self.async_show_form(step_id="otp", data_schema=VOL_SCHEMA_HOMECONFIG_OTP, errors=errors)

    async def async_step_centrale(self, user_input=None):
        """terzo step: seleziona la centrale."""
        errors = {}

        _LOGGER.debug(f"lancio get centrali")
        await self.hass.async_add_executor_job(self.myTCSSession.get_centrali)

        options_dict = {
            f"{seriale} - {self.myTCSSession.centrali[seriale].tp.description}": seriale
            for seriale in self.myTCSSession.centrali
        }
        _LOGGER.debug(f"fatto ho {len(self.myTCSSession.centrali)} centrali")

        if len(self.myTCSSession.centrali) == 0:
            _LOGGER.debug(f"non sono presenti centrali")
            return self.async_abort(reason="non sono presenti centrali")
        elif len(self.myTCSSession.centrali) == 1:
            _LOGGER.debug(f"presente una sola centrale, non serve selezionarla")
        else:
            if user_input is not None:
                selected_seriale = options_dict[user_input["Centrale"]]

                return self.async_create_entry(title=self.user_data["homeName"],
                                               data={
                                                   "token": self.myTCSSession.token,
                                                    "appid": self.myTCSSession.appid,
                                                    "centrale": selected_seriale
                                                    })
            schema = vol.Schema({
                vol.Required("Centrale"): vol.In(options_dict)  # Usa i valori dinamici
            })

            return self.async_show_form(
                step_id="centrale",
                data_schema=schema,
                errors=errors
            )
