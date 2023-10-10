
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
from enum import Enum


import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"

class Groups(Enum):
    PIEPERS = ("PIEPERS")
    INIS = ("INIs")
    STD_MEMBERS = ("STANDARD MEMBERS")
    SUPPORTING_MEMBERS = ("SUPPORTING MEMBERS")
    

def check_settings(config, hass):
    if not any(config.get(i) for i in ["username"]):
        _LOGGER.error("username was not set")
        raise vol.Invalid("Missing settings to setup the sensor.")
        
    if not config.get("password"):
        _LOGGER.error("password was not set")
        raise vol.Invalid("Missing settings to setup the sensor.")
        

class ComponentSession(object):
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Python/3"
        self.s.headers["Accept-Language"] = "en-US,en;q=0.9"

    

    def login(self, username, password):
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}
        response = self.s.get("https://jnm.be/nl/inloggen",headers=header,timeout=10,allow_redirects=False)
        _LOGGER.debug(f"jnm.be login get result status code: {response.status_code}")
        _LOGGER.debug(f"jnm.be login header: {response.headers}")
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the meta tag with the name="csrf-token" attribute
        csrf_token_meta = soup.find('meta', {'name': 'csrf-token'})
        assert csrf_token_meta != None
        # Extract the content of the csrf-token meta tag
        csrf_token = csrf_token_meta['content']

        
        header = {"Content-Type": "application/x-www-form-urlencoded", "Referer": "https://jnm.be/nl/inloggen", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}
        
        response = self.s.post("https://jnm.be/accept-cookies",headers=header,data=f"_token={csrf_token}&project-locale=0&google-analytics=0&google-analytics=0&youtube=0&youtube=0&vimeo=0&vimeo=0", timeout=15,allow_redirects=False)
        _LOGGER.debug(f"jnm.be accept-cookies post result status code: {response.status_code}")
        _LOGGER.debug(f"jnm.be accept-cookies header: {response.headers}")
        _LOGGER.debug(f"jnm.be accept-cookies text: {response.text}")
        assert response.status_code == 302

        response = self.s.get("https://jnm.be/nl/inloggen",headers=header,timeout=10,allow_redirects=True)
        _LOGGER.debug(f"jnm.be login get result status code: {response.status_code}")
        _LOGGER.debug(f"jnm.be login header: {response.headers}")
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the meta tag with the name="csrf-token" attribute
        csrf_token_meta = soup.find('meta', {'name': 'csrf-token'})
        assert csrf_token_meta != None
        # Extract the content of the csrf-token meta tag
        csrf_token = csrf_token_meta['content']
        
    
        response = self.s.post("https://jnm.be/nl/inloggen",headers=header,data=f"_token={csrf_token}&username={username}&password={password}&login=", timeout=15,allow_redirects=False)
        _LOGGER.debug(f"jnm.be login post result status code: {response.status_code}")
        _LOGGER.debug(f"jnm.be login header: {response.headers}")
        _LOGGER.debug(f"jnm.be login text: {response.text}")
        assert response.status_code == 302
        

        response = self.s.get("https://jnm.be/nl/mijn-profielpagina",headers=header, timeout=15,allow_redirects=False)
        _LOGGER.debug(f"jnm.be profile get status code: {response.status_code}")
        _LOGGER.debug(f"jnm.be profile header: {response.headers}")
        _LOGGER.debug(f"jnm.be profile text: {response.text}")
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Create a dictionary to store the extracted data
        data = {}

        # Extract relevant data
        # Find the unsorted list with the specified class
        ulist = soup.find('ul', class_='list-unstyled list--icon mb-4')

        if ulist:
            # Extract the second list item as the "name" value
            list_items = ulist.find_all('li')
            if len(list_items) >= 2:
                data['user_details'] = {
                    'name': list_items[1].text.strip(),
                    'birth_date': soup.find('time').text.strip()
                }
            else:
                data['user_details'] = {
                    'name': 'Name not found',
                    'birth_date': 'Birth date not found'
                }
        data['membership'] = {
            'username': soup.find('dd').text.strip(),
            'membership_number': soup.find_all('strong')[1].text.strip(),
            'membership_fee': soup.find_all('dd', class_='ms-2')[1].text.strip()
        }
        department = soup.find('div', class_='member__department')
        data['department'] = {
                'department_title': department.h3.a.text.strip(),
                'age_group': department.dl.dd.text.strip()
            }

        return data

    def getActivities(self, age_group, department):
        "https://jnm.be/nl/activiteiten?group={Piepers}&department=jnm-zuidwest-brabant"
        "https://jnm.be/nl/activiteiten?group={age_group}&department={department}"
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}
               

        response = self.s.get("https://jnm.be/nl/activiteiten?group={age_group}&department={department}",headers=header, timeout=15,allow_redirects=False)
        _LOGGER.debug(f"jnm.be activities get status code: {response.status_code}")
        _LOGGER.debug(f"jnm.be activities header: {response.headers}")
        _LOGGER.debug(f"jnm.be activities text: {response.text}")
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Create a dictionary to store the extracted data
        data = {}

        # Extract relevant data
        # Find the unsorted list with the specified class
        ulist = soup.find('ul', class_='list-unstyled list--icon mb-4')

        if ulist:
            # Extract the second list item as the "name" value
            list_items = ulist.find_all('li')
            if len(list_items) >= 2:
                data['user_details'] = {
                    'name': list_items[1].text.strip(),
                    'birth_date': soup.find('time').text.strip()
                }
            else:
                data['user_details'] = {
                    'name': 'Name not found',
                    'birth_date': 'Birth date not found'
                }
        data['membership'] = {
            'username': soup.find('dd').text.strip(),
            'membership_number': soup.find_all('strong')[1].text.strip(),
            'membership_fee': soup.find_all('dd', class_='ms-2')[1].text.strip()
        }
        department = soup.find('div', class_='member__department')
        data['department'] = {
                'department_title': department.h3.a.text.strip(),
                'age_group': department.dl.dd.text.strip()
            }

        return data
        