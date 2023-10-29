import logging
import json
from pathlib import Path
import re

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.const import Platform
from .utils import *

# manifestfile = Path(__file__).parent / 'manifest.json'
# with open(manifestfile, 'r') as json_file:
#     manifest_data = json.load(json_file)
    
# DOMAIN = "manifest_data.get("domain")"
# NAME = manifest_data.get("name")
# VERSION = manifest_data.get("version")
# ISSUEURL = manifest_data.get("issue_tracker")
DOMAIN = "jnm"
NAME = "JNM"

PLATFORMS = [Platform.SENSOR]

STARTUP = """
-------------------------------------------------------------------
{name}
-------------------------------------------------------------------
""".format(
    name=NAME
)


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up this component using YAML."""
    _LOGGER.info(STARTUP)
    if config.get(DOMAIN) is None:
        # We get her if the integration is set up using config flow
        return True

    try:
        await hass.config_entries.async_forward_entry(config, Platform.SENSOR)
        _LOGGER.info("Successfully added sensor from the integration")
    except ValueError:
        pass

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )
    return True

async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload integration when options changed"""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    # if unload_ok:
        # hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up component as config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, Platform.SENSOR)
    )
    _LOGGER.info(f"{DOMAIN} register_services")
    register_services(hass, config_entry)
    return True


async def async_remove_entry(hass, config_entry):
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, Platform.SENSOR)
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass


def register_services(hass, config_entry):
        
    async def handle_subscribe_activity(call):
        """Handle the service call."""
        activity_url = call.data.get('activity_url')
        
        config = config_entry.data
        username = config.get("username")
        password = config.get("password")
        session = ComponentSession()
        userdetails = await hass.async_add_executor_job(lambda: session.login(username, password))
        assert userdetails is not None
        _LOGGER.debug(f"{NAME} handle_subscribe_activity login completed")
        subscribe_activity_feedback = await hass.async_add_executor_job(lambda: session.subscribe_activity(activity_url))
        # state_warning_sensor = hass.states.get(f"sensor.{DOMAIN}_warning")
        # _LOGGER.debug(f"state_warning_sensor sensor.{DOMAIN}_warning {state_warning_sensor}")
        # state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
        # state_warning_sensor_attributes["refresh_required"] = state_warning_sensor_attributes.get("refresh_required", False) or (extension_confirmation > 0)
        # _LOGGER.debug(f"state_warning_sensor attributes sensor.{DOMAIN}_warning: {state_warning_sensor_attributes}")
        # await hass.async_add_executor_job(lambda: hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))

                            

    async def handle_update(call):
        """Handle the service call."""
        # state_warning_sensor = hass.states.get(f"sensor.{DOMAIN}_warning")
        # _LOGGER.debug(f"state_warning_sensor sensor.{DOMAIN}_warning {state_warning_sensor}")
        # state_warning_sensor_attributes = dict(state_warning_sensor.attributes)
        # state_warning_sensor_attributes["refresh_required"] = True
        # await hass.async_add_executor_job(lambda: hass.states.set(f"sensor.{DOMAIN}_warning",state_warning_sensor.state,state_warning_sensor_attributes))


    hass.services.async_register(DOMAIN, 'subscribe_activity', handle_subscribe_activity)
    hass.services.async_register(DOMAIN, 'update', handle_update)
    _LOGGER.info(f"async_register done")
