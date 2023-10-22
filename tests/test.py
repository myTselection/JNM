import unittest
import requests
import logging
import json
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup
# from "../custom_components/telenet_telemeter/utils" import .
# import sys
# sys.path.append('../custom_components/telenet_telemeter/')
# from utils import ComponentSession, dry_setup
# from sensor import *

_LOGGER = logging.getLogger(__name__)

hass = "test"
def async_add_devices(sensors): 
     _LOGGER.debug(f"session.userdetails {json.dumps(sensorsindent=4)}")

#run this test on command line with: python -m unittest test_component_session

logging.basicConfig(level=logging.DEBUG)

def login():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    userdetails = dict()

    header = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}
    response = s.get("https://jnm.be/nl/inloggen",headers=header,timeout=10,allow_redirects=False)
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
    
    response = s.post("https://jnm.be/accept-cookies",headers=header,data=f"_token={csrf_token}&project-locale=0&google-analytics=0&google-analytics=0&youtube=0&youtube=0&vimeo=0&vimeo=0", timeout=15,allow_redirects=False)
    _LOGGER.debug(f"jnm.be login post result status code: {response.status_code}")
    _LOGGER.debug(f"jnm.be login header: {response.headers}")
    _LOGGER.debug(f"jnm.be login text: {response.text}")
    assert response.status_code == 302

    response = s.get("https://jnm.be/nl/inloggen",headers=header,timeout=10,allow_redirects=True)
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

    #TODO
    username = ""
    password = ""
    
 
    response = s.post("https://jnm.be/nl/inloggen",headers=header,data=f"_token={csrf_token}&username={username}&password={password}&login=", timeout=15,allow_redirects=False)
    _LOGGER.debug(f"jnm.be login post result status code: {response.status_code}")
    _LOGGER.debug(f"jnm.be login header: {response.headers}")
    _LOGGER.debug(f"jnm.be login text: {response.text}")
    assert response.status_code == 302
    

    response = s.get("https://jnm.be/nl/mijn-profielpagina",headers=header, timeout=15,allow_redirects=False)
    _LOGGER.debug(f"jnm.be profile post get status code: {response.status_code}")
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
    

    
    department = data.get('department').get('department_title').replace(' ','-').lower()
    age_group = data.get('department').get('age_group').lower()

    response = s.get(f"https://jnm.be/nl/activiteiten?group={age_group}&department={department}",headers=header, timeout=15,allow_redirects=False)
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
    cards = soup.find_all('div', class_='card card--activity--calendar')

    for card in cards:
        # Extract date
        date_element = card.find('time')
        date = date_element.get_text(strip=True)

        # Extract name
        name_element = card.find('h2').find('a')
        name = name_element.get_text(strip=True)

        # Extract group
        group_element = card.find('span', class_='card--activity--calendar__info')
        group = group_element.get_text(strip=True)

    url = "https://jnm.be/nl/activiteiten/van-markt-tot-kookpot"
    
    response = s.get(f"{url}",headers=header, timeout=15,allow_redirects=False)
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
    start_date, start_time, end_time = date_time
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
        data['num_participants'] = int(num_participants.text.strip())

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

    # Extract activity description
    activity_description = soup.find('div', class_='text-columns__1')
    if activity_description:
        data['activity_description2'] = activity_description.text.strip()

    # Extract responsible person(s)
    responsible_persons = []
    responsible_person_elements = soup.find_all('strong')
    for element in responsible_person_elements:
        responsible_person = element.text.strip()
        if "(Activiteitverantwoordelijke)" in responsible_person:
            responsible_person = responsible_person.replace("(Activiteitverantwoordelijke)", "").strip()
        responsible_persons.append(responsible_person)
    data['responsible_persons2'] = responsible_persons
    return data

# Define a function to convert BeautifulSoup tree to JSON
def html_to_json(element):
    result = {}
    if element.name:
        result[element.name] = {}
        if element.attrs:
            result[element.name]["attributes"] = element.attrs
        if element.contents:
            if len(element.contents) == 1 and element.contents[0].string:
                result[element.name]["text"] = element.contents[0]
            else:
                result[element.name]["children"] = [html_to_json(child) for child in element.contents if child.name or (str(child).strip() != '')]
    return result


def old():
    #authorize based on url in location of response received
    response = s.get(oauth_location,headers=header,timeout=10,allow_redirects=False)
    _LOGGER.debug(f"bibliotheek.be auth get result status code: {response.status_code}")
    _LOGGER.debug(f"bibliotheek.be auth get header: {response.headers}")
    assert response.status_code == 200
    
    # data = f"hint={hint}&token={oauth_token}&callback=https%3A%2F%2Fbibliotheek.be%2Fmy-library%2Flogin%2Fcallback&email={username}&password={password}"
    data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": USERNAME, "password": PASSWORD}
    #login
    #example header response: https://bibliotheek.be/my-library/login/callback?oauth_token=f68491752279e1a5c0a4ee9b6a349836&oauth_verifier=d369ffff4a5c4a05&uilang=nl
    response = s.post('https://mijn.bibliotheek.be/openbibid/rest/auth/login',headers=header,data=data,timeout=10,allow_redirects=False)
    _LOGGER.debug(f"bibliotheek.be login get result status code: {response.status_code}")
    _LOGGER.debug(f"bibliotheek.be login get header: {response.headers}")
    login_location = response.headers.get('location')
    login_locatonurl_parsed = urlsplit(login_location)
    login_query_params = parse_qs(login_locatonurl_parsed.query)
    oauth_verifier = login_query_params.get('oauth_verifier')
    oauth_token = query_params.get('oauth_token')
    hint = query_params.get('hint')
    _LOGGER.debug(f"bibliotheek.be url params parsed: login_location: {login_location}, oauth_token: {oauth_token}, oauth_verifier: {oauth_verifier}")
    #example login_location: https://bibliotheek.be/my-library/login/callback?oauth_token=***************&oauth_verifier=*********&uilang=nl
    assert response.status_code == 303
    
    #login callback based on url in location of response received
    response = s.get(login_location,headers=header,timeout=10,allow_redirects=False)
    login_callback_location = response.headers.get('location')
    _LOGGER.debug(f"bibliotheek.be login callback get result status code: {response.status_code}")
    _LOGGER.debug(f"bibliotheek.be login callback get header: {response.headers} text {response.text}")
    assert response.status_code == 302
    # if response.status_code == 302:        
    #     # request access code, https://mijn.bibliotheek.be/openbibid-api.html#_authenticatie
    #     data = {"hint": hint, "token": oauth_token, "callback":"https://bibliotheek.be/my-library/login/callback", "email": username, "password": password}
    #     response = s.post('https://mijn.bibliotheek.be/openbibid/rest/accessToken',headers=header,data=data,timeout=10,allow_redirects=False)
    #     _LOGGER.debug(f"bibliotheek.be login get result status code: {response.status_code}")
    # else:
    #     #login session was already available
    #     login_callback_location = "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen"
    login_callback_location = "https://bibliotheek.be/mijn-bibliotheek/lidmaatschappen"
    #lidmaatschap based on url in location of response received
    response = s.get(f"{login_callback_location}",headers=header,timeout=10,allow_redirects=False)
    lidmaatschap_response_header = response.headers
    _LOGGER.debug(f"bibliotheek.be lidmaatschap get result status code: {response.status_code}") # response: {response.text}")
    _LOGGER.debug(f"bibliotheek.be lidmaatschap get header: {response.headers}")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, 'html.parser')
    
    
    #find all accounts
    accounts = soup.find_all('div', class_='my-library-user-library-account-list__account')
    _LOGGER.debug(f"accounts found: {accounts}")


login()