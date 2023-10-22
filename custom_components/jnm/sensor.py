import logging
import asyncio
from datetime import date, datetime, timedelta
from .utils import *

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.util import Throttle
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME
)

from . import DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"



PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("username"): cv.string,
        vol.Required("password"): cv.string,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(hours=1)
# MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)



async def dry_setup(hass, config_entry, async_add_devices):
    config = config_entry
    username = config.get("username")
    password = config.get("password")

    check_settings(config, hass)
    sensors = []
    
    componentData = ComponentData(
        username,
        password,
        hass
    )
    await componentData._forced_update()

    
    _LOGGER.debug(f"userdetails dry_setup {componentData._userdetails}") 

    #TODO create sensors
    userSensor = ComponentUserSensor(componentData)
    sensors.append(userSensor)
    activitySensor = ComponentActivitySensor(componentData)
    sensors.append(activitySensor)
    subscribedActivitySensor = ComponentSubscribedActivitySensor(componentData)
    sensors.append(subscribedActivitySensor)

    async_add_devices(sensors)


async def async_setup_platform(
    hass, config_entry, async_add_devices, discovery_info=None
):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_platform " + NAME)
    await dry_setup(hass, config_entry, async_add_devices)
    return True


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_entry " + NAME)
    config = config_entry.data
    await dry_setup(hass, config, async_add_devices)
    return True


async def async_remove_entry(hass, config_entry):
    _LOGGER.info("async_remove_entry " + NAME)
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass
        

def convert_string_to_date(string_date):
    day, month, year = map(int, string_date.split('/'))
    return date(year, month, day)

def convert_string_to_date_yyyy_mm_dd(string_date):
    year, month, day = map(int, string_date.split('/'))
    return date(year, month, day)

def calculate_days_remaining(target_date):
    today = date.today()
    remaining_days = (target_date - today).days
    return remaining_days

class ComponentData:
    def __init__(self, username, password, hass):
        self._username = username
        self._password = password
        self._hass = hass
        self._session = ComponentSession()
        self._userdetails = None
        self._activities = None
        self._subscribed_activities = None
        self._last_update = None
        self._refresh_required = True
        self._refresh_retry = 0

    @property
    def unique_id(self):
        return f"{NAME} {self._username}"
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id

    # same as update, but without throttle to make sure init is always executed
    async def _forced_update(self):
        _LOGGER.info("Fetching init stuff for " + NAME)
        self._refresh_retry += 1
        if not(self._session):
            self._session = ComponentSession()
        
        self._last_update = datetime.now()
        if self._session:
            _LOGGER.debug("Getting data for " + NAME)
            try:
                self._userdetails = await self._hass.async_add_executor_job(lambda: self._session.login(self._username, self._password))
                self._activities = await self._hass.async_add_executor_job(lambda: self._session.getActivities(self._userdetails))
                self._subscribed_activities = await self._hass.async_add_executor_job(lambda: self._session.getSubscribedActivities())
                self._refresh_retry = 0
                self._refresh_required = False
            except Exception as e:
                # Log the exception details
                _LOGGER.warning(f"An exception occurred, will retry: {str(e)}", exc_info=True)
                self._refresh_required = True
            _LOGGER.debug("Data fetched completed " + NAME)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update(self):
        await self._forced_update()

    async def update(self):
        # force update if (some) values are still unknown
        if (self._userdetails is None or self._userdetails is {} or self._refresh_required) and self._refresh_retry < 5:
            await self._forced_update()
        else:
            await self._update()

    def clear_session(self):
        self._session : None

class ComponentUserSensor(Entity):
    def __init__(self, data):
        self._data = data
        self._userdetails = data._userdetails
        self._last_update =  self._data._last_update
        self._age_group = None
        self._department_title = None
        self._name = None
        self._username = None
        self._membership_number = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._age_group

    async def async_update(self):
        await self._data.update()
        self._userdetails = self._data._userdetails
        self._last_update =  self._data._last_update
        self._age_group = self._userdetails.get('department').get('age_group')
        self._department_title = self._userdetails.get('department').get('department_title')
        self._name = self._userdetails.get('user_details').get('name')
        self._username = self._userdetails.get('membership').get('username')
        self._membership_number = self._userdetails.get('membership').get('membership_number')


    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()

    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:account-circle"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self._data.unique_id} group"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "age_group": self._age_group,
            "department": self._department_title,
            "name": self._name,
            "username": self._username,
            "membership_number": self._membership_number
        }

   
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )

    @property
    def friendly_name(self) -> str:
        return self.unique_id

class ComponentActivitySensor(Entity):
    def __init__(self, data):
        self._data = data
        self._userdetails = data._userdetails
        self._activities = data._activities
        self._last_update =  self._data._last_update
        self._next_activity_date = None
        self._next_activity_name = None
        self._next_activity_group = None
        self._next_activity_link = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._next_activity_date

    async def async_update(self):
        await self._data.update()
        self._userdetails = self._data._userdetails
        self._activities = self._data._activities
        self._last_update =  self._data._last_update
        
        self._next_activity_date = self._activities[0].get('date')
        self._next_activity_name = self._activities[0].get('name')
        self._next_activity_group = self._activities[0].get('group')
        self._next_activity_link = self._activities[0].get('link')


    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()

    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:account-circle"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self._data.unique_id} next activity"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "next activity date": self._next_activity_date,
            "next activity name": self._next_activity_name,
            "next activity group": self._next_activity_group,
            "next activity link": self._next_activity_link,
            "future activities": self._activities
        }

   
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )

    @property
    def friendly_name(self) -> str:
        return self.unique_id

class ComponentSubscribedActivitySensor(Entity):
    def __init__(self, data):
        self._data = data
        self._userdetails = data._userdetails
        self._activities = data._activities
        self._last_update =  self._data._last_update
        self._last_activity_date = None
        self._last_activity_name = None
        self._last_activity_group = None
        self._last_activity_link = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._last_activity_date

    async def async_update(self):
        await self._data.update()
        self._userdetails = self._data._userdetails
        self._activities = self._data._subscribed_activities
        self._last_update =  self._data._last_update
        
        self._last_activity_date = self._activities[0].get('date')
        self._last_activity_name = self._activities[0].get('name')
        self._last_activity_group = self._activities[0].get('group')
        self._last_activity_link = self._activities[0].get('link')


    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()

    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:account-circle"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self._data.unique_id} last subscribed activity"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "last activity date": self._last_activity_date,
            "last activity name": self._last_activity_name,
            "last activity group": self._last_activity_group,
            "last activity link": self._last_activity_link,
            "past activities": self._activities
        }

   
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=self._data.name,
            manufacturer= NAME
        )

    @property
    def friendly_name(self) -> str:
        return self.unique_id
