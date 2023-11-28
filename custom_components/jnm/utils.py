
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
        self.s = requests.Session()
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

    def getActivities(self, user_details):
        department = user_details.get('department').get('department_title').replace(' ','-').lower()
        age_group = user_details.get('department').get('age_group').lower()
        
        activities = self.getActivityData(f"https://jnm.be/nl/activiteiten?group={age_group}&department={department}")

        for activity in activities:
            activity_details = self.getActivityDetailsData(activity.get('link'))
            activity['details'] = activity_details

        return activities
        
    def getSubscribedActivities(self):
        activities = self.getActivityData("https://jnm.be/nl/mijn-activiteiten")

        return activities
        
    def getActivityData(self, url):
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}
               

        response = self.s.get(f"{url}",headers=header, timeout=15,allow_redirects=False)
        _LOGGER.debug(f"jnm.be activities get status code: {response.status_code}, url: {url}")
        _LOGGER.debug(f"jnm.be activities header: {response.headers}")
        _LOGGER.debug(f"jnm.be activities text: {response.text}")
        assert response.status_code == 200

        activities = []

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')


        # Extract relevant data
        # Find the unsorted list with the specified class
        cards = soup.find_all('div', class_='card card--activity--calendar')

        for card in cards:
            # Extract date
            date_element = card.find('time')
            date = date_element.get_text(strip=True)
            # Split the date by " - " and keep the second part
            date_parts = date.split(' - ')
            if len(date_parts) == 2:
                date = date_parts[1]
            # Convert the cleaned date string to a date object
            date = datetime.strptime(date, "%d.%m.%Y")


            # Extract name
            name_element = card.find('h2').find('a')
            name = name_element.get_text(strip=True)
            # Extract link
            link_element = name_element['href']

            # Extract group
            group_element = card.find('span', class_='card--activity--calendar__info')
            group = group_element.get_text(strip=True)
            activities.append({"date": date, "name": name, "group": group, "link": link_element})

        return activities
    
    
    def getActivityDetailsData(self, url):
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

        header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}
               

        response = self.s.get(f"{url}",headers=header, timeout=15,allow_redirects=False)
        _LOGGER.debug(f"jnm.be activities details get status code: {response.status_code}, url: {url}")
        _LOGGER.debug(f"jnm.be activities header: {response.headers}")
        _LOGGER.debug(f"jnm.be activities text: {response.text}")
        assert response.status_code == 200

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        card = soup.find('div', class_='container mt-6 mb-140 activity-show')

        # Create a dictionary to store the extracted information
        data = {}

        # Extract activity type
        activity_type = card.find('p', class_='activity__type').text
        data['activity_type'] = activity_type

        # Extract activity name
        activity_name = soup.find('h1').text
        data['activity_name'] = activity_name

        # Extract date and time
        date_time = soup.find('time').text.strip().replace(' ','').replace('\ntot','').split('\n')
        if len(date_time) == 3:
            start_date, start_time, end_time = date_time
        if len(date_time) == 4:
            start_date, start_time, end_date, end_time = date_time
            data['end_date'] = end_date
        
        data['start_date'] = start_date
        data['start_time'] = start_time
        data['end_time'] = end_time

        # Extract theme if available
        theme = soup.select_one('.activity-show dt:contains("Thema") + dd')
        if theme:
            data['theme'] = theme.text.strip()

        # Extract organized by
        organized_by = soup.select_one('.activity-show dt:contains("Georganiseerd door") + dd')
        if organized_by:
            data['organized_by'] = organized_by.text.strip()

        # Extract participating department
        participating_department = soup.select_one('.activity-show dt:contains("Deelnemende afdeling") + dd')
        if participating_department:
            data['participating_department'] = participating_department.text.strip()

        # Extract age group
        age_group = soup.select_one('.activity-show dt:contains("Leeftijdsgroep") + dd')
        if age_group:
            data['age_group'] = age_group.text.strip()

        # Extract location
        location = soup.select_one('.activity-show dt:contains("Locatie") + dd')
        if location:
            data['location'] = location.text.strip()

        # Extract number of participants
        num_participants = soup.select_one('.activity-show dt:contains("Aantal deelnemers") + dd')
        if num_participants:
            data['num_participants'] = int(num_participants.text.replace('1 / ','').replace('/','').replace(' ','').strip())

        # Extract whether to bring a bicycle
        bring_bicycle = soup.select_one('.activity-show dt:contains("Fiets meenemen") + dd')
        if bring_bicycle:
            data['bring_bicycle'] = bring_bicycle.text.strip()

        # Extract activity description
        activity_description = soup.select_one('.activity-show .text-columns__1')
        if activity_description:
            data['activity_description'] = activity_description.text.strip()

        # Extract responsible person(s)
        responsible_persons = [element.get_text(strip=True) for element in soup.select('.activity-show strong')]
        data['responsible_persons'] = responsible_persons

        # # Extract activity description
        # activity_description = soup.find('div', class_='text-columns__1')
        # if activity_description:
        #     data['activity_description2'] = activity_description.text.strip()

        # # Extract responsible person(s)
        # responsible_persons = []
        # responsible_person_elements = soup.find_all('strong')
        # for element in responsible_person_elements:
        #     responsible_person = element.text.strip()
        #     if "(Activiteitverantwoordelijke)" in responsible_person:
        #         responsible_person = responsible_person.replace("(Activiteitverantwoordelijke)", "").strip()
        #     responsible_persons.append(responsible_person)
        # data['responsible_persons2'] = responsible_persons
        return data
        