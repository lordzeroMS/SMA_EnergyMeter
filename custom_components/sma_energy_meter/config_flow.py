"""Config flow for SMA Energy Meter integration."""
import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_HOST

from .coordinator import SMAEnergyMeterCoordinator
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SMAEnergyMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMA Energy Meter."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]

            try:
                # Test connection
                coordinator = SMAEnergyMeterCoordinator(self.hass, host)
                await self.hass.async_add_executor_job(coordinator._setup_socket)

                if coordinator._socket is not None:
                    # Clean up socket
                    await coordinator.async_stop()

                    return self.async_create_entry(
                        title=f"SMA Energy Meter ({host})",
                        data={CONF_HOST: host}
                    )
                else:
                    errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(CONF_HOST, default="0.0.0.0"): str,
            }),
            errors=errors,
        )

    async def async_step_import(self, import_info):
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)