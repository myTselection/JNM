
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
        
        

    def get_data(self, config, contract_type: ContractType):
        postalcode = config.get("postalcode")
        electricity_digital_counter = config.get("electricity_digital_counter", False)
        electricity_digital_counter_n = 1 if electricity_digital_counter == True else 0
        day_electricity_consumption = config.get("day_electricity_consumption",0)
        night_electricity_consumption = config.get("night_electricity_consumption", 0)
        excl_night_electricity_consumption = config.get("excl_night_electricity_consumption", 0)

        solar_panels = config.get("solar_panels", False)
        solar_panels_n = 1 if solar_panels == True else 0
        electricity_injection = config.get("electricity_injection", 0)
        electricity_injection_night = config.get("electricity_injection_night", 0)

        electricity_provider = config.get("electricity_provider", "No provider")
        electricity_provider_n = providers.get(electricity_provider,0)

        inverter_power = config.get("inverter_power", 0)
        inverter_power = str(inverter_power).replace(',','%2C').replace('.','%2C')

        combine_elec_and_gas = config.get("combine_elec_and_gas", False)     
        combine_elec_and_gas_n = 1 if combine_elec_and_gas == True else 0   
        
        gas_consumption = config.get("gas_consumption", 0)
        
        gas_provider = config.get("gas_provider", "No provider")
        gas_provider_n = providers.get(gas_provider,0)

        directdebit_invoice = config.get("directdebit_invoice", True)
        directdebit_invoice_n = 1 if directdebit_invoice == True else 0
        email_invoice = config.get("email_invoice", True)
        email_invoice_n = 1 if email_invoice == True else 0
        online_support = config.get("online_support", True)
        online_support_n = 1 if online_support == True else 0
        electric_car = config.get("electric_car", False)
        electric_car_n = 1 if electric_car == True else 0

        electricity_comp = day_electricity_consumption != 0 or night_electricity_consumption != 0 or excl_night_electricity_consumption != 0
        gas_comp = gas_consumption != 0

        types_comp = []
        if electricity_comp: 
            types_comp.append("elektriciteit")
        if gas_comp:
            types_comp.append("aardgas")
    
        elec_level = 0
        if night_electricity_consumption != 0:
            elec_level += 1
        if excl_night_electricity_consumption !=0:
            elec_level += 1

        result = {}
        for type_comp in types_comp:
            myenergy_url = f"https://www.mijnenergie.be/energie-vergelijken-3-resultaten-?Form=fe&e={type_comp}&d={electricity_digital_counter_n}&c=particulier&cp={postalcode}&i2={elec_level}----{day_electricity_consumption}-{night_electricity_consumption}-{excl_night_electricity_consumption}-1----{gas_consumption}----1-{directdebit_invoice_n}%7C{email_invoice_n}%7C{online_support_n}%7C1-{electricity_injection}%7C{electricity_injection_night}%7C{solar_panels_n}%7C%7C0%21{contract_type.code}%21A%21n%7C0%21{contract_type.code}%21A%7C{combine_elec_and_gas_n}%7C{inverter_power}%7C%7C%7C%7C%7C%21%7C%7C{inverter_power}%7C%7C{electric_car_n}-{electricity_provider_n}%7C{gas_provider_n}-0"
            
            _LOGGER.debug(f"myenergy_url: {myenergy_url}")
            response = self.s.get(myenergy_url,timeout=30,allow_redirects=True)
            assert response.status_code == 200
            
            _LOGGER.debug("get result status code: " + str(response.status_code))
            # _LOGGER.debug("get result response: " + str(response.text))
            soup = BeautifulSoup(response.text, 'html.parser')


            
            # sections = soup.find_all('div', class_='container-fluid container-fluid-custom')
            # for section in sections:
            
            section_ids = []
            # if electricity_comp:
            #     section_ids.append("RestultatElec")
            # if gas_comp:
            #     section_ids.append("RestultatGas")
            # if combine_elec_and_gas:
            #     section_ids = ["RestultatDualFuel"]
            section_ids.append("ScrollResult")
            for section_id in section_ids:
                _LOGGER.debug(f"section_id {section_id}")
                section =  soup.find(id=section_id)
                # if section == None:
                    # continue

                # sectionName = section.find("caption", class_="sr-only").text
                sectionName = section.find("h3", class_="h4 text-strong").text
                sectionName = sectionName.replace('Resultaten ','').title()
                # providerdetails = section.find_all('tr', class_='cleantable_overview_row')
                providerdetails = section.find_all('div', class_='card-body')
                providerdetails_array = []
                for providerdetail in providerdetails:
                    providerdetails_name = providerdetail.find('li', class_='list-inline-item large-body-font-size text-strong mb-2 mb-sm-0').text
                    providerdetails_name = providerdetails_name.replace('\n', '')

                    # Find the <img> element within the specified <div> by class name
                    img_element = providerdetail.find('div', class_='provider-logo-lg').find('img')

                    # Extract the 'alt' attribute, which contains the provider name
                    provider_name = img_element['alt']
                    provider_name = provider_name.replace('Logo ','').title()


                    # Find all table rows and extract the data
                    table_rows = providerdetail.find_all('tr')

                    # Create a list to store the table data
                    # table_data = []
                    json_data = {}
                    json_data['name'] = providerdetails_name
                    json_data['url'] = myenergy_url
                    json_data['provider'] = provider_name

                    heading_index = 0
                    # Loop through the rows and extract the data into a dictionary
                    for row in table_rows:
                        columns = row.find_all(['th', 'td'])
                        row_data = []
                        for column in columns:
                            data = column.get_text().strip()
                            if data != "":
                                row_data.append(data.replace("\xa0", "").replace("+ ", "").replace("â‚¬","€"))
                        if len(row_data) > 0:
                            if len(row_data) == 1 and heading_index <= (len(headings)-1) and row_data[0] != headings[heading_index] and '€' in row_data[0] and 'korting' not in row_data[0] and 'promo' not in row_data[0] and len(row_data[0]) < 10:
                                json_data[headings[heading_index]] = row_data[0]
                                heading_index += 1
                            else:
                                json_data[row_data[0]] = row_data[1:]
                        # table_data.append(row_data)
                    heading_index = 0
                    providerdetails_array.append(json_data)
                    #only first restult is needed, if all details are required, remove the break below
                    break
                result[sectionName] = providerdetails_array
        return result

        