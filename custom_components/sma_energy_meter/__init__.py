"""SMA Energy Meter integration."""
import logging
import asyncio
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST
import homeassistant.helpers.config_validation as cv

from .coordinator import SMAEnergyMeterCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "sma_energy_meter"
PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST, default="0.0.0.0"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the SMA Energy Meter component."""
    if DOMAIN not in config:
        return True

    host = config[DOMAIN].get(CONF_HOST)

    coordinator = SMAEnergyMeterCoordinator(hass, host)
    await coordinator.async_start()

    hass.data[DOMAIN] = coordinator

    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, config)
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SMA Energy Meter from a config entry."""
    host = entry.data.get(CONF_HOST, "0.0.0.0")

    coordinator = SMAEnergyMeterCoordinator(hass, host)
    await coordinator.async_start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_stop()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok