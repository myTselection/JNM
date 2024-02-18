[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/myTselection/JNM.svg)](https://github.com/myTselection/JNM/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/JNM.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/JNM.svg)](https://github.com/myTselection/JNM/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/JNM.svg)](https://github.com/myTselection/JNM/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/JNM.svg)](https://github.com/myTselection/JNM/graphs/commit-activity)

# JNM - Home Assistant integration
[JNM](https://www.jnm.be/) Home Assistant custom component integration for Belgium. JNM is a Belgian youth union for Nature and the Environment, https://jnm.be/nl/dat-is-jnm This custom component has been built from the ground up to bring jnm.be activities listed on the site into Home Assistant sensors in order to follow up activities and subscribe. This integration is built against the public website provided by jnm.be for Belgium and has not been tested for any other countries.

This integration is in no way affiliated with JNM. **Please don't report issues with this integration to JNM, they will not be able to support you.**

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/JNM/master/icon.png"/></p>


## Installation
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/JNM as custom repository (HACS > Integration > option: Custom Repositories)
	- [![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=myTselection&repository=JNM&category=integration)

- Restart Home Assistant
- Add 'JNM' integration via HA Settings > 'Devices and Services' > 'Integrations'



## Integration
Device `JNM` should become available with the following sensors:
- <details><summary><code>JNM_[username]_group</code> with details </summary>


	| Attribute | Description |
	| --------- | ----------- |
	| State     | Age group  |
	| Last update   | Timestamp of last data refresh, throttled to limit data fetch to 1h |
  | age_group  | Age group  |
  | Department | Department |
  | Name       | Name       |
  | Username   | Username   |
  | Membership number | Membership number |
	
</details>

- <details><summary><code>JNM_[username]_next_activity</code> with details </summary>


	| Attribute | Description |
	| --------- | ----------- |
	| State     | Date next activity  |
	| Last update   | Timestamp of last data refresh, throttled to limit data fetch to 1h |
  | next activity date  | Date of the next activity  |
  | next activity name  | Name of the next activity |
  | next activity group | Group of the next activity  |
  | next activity link  | Link of the next activity   |
  | future activities   | Details of the next activity with: date, name, group, link, details. The details contain: activity_type, activity_name, start_date, start_time, end_time, theme, organized_by, participating_department, age_group, location, num_participants, bring_bicycle, activity_description, responsible_persons   |
	
</details>

- <details><summary><code>JNM_[username]_last_subscribed_activity</code> with details </summary>


	| Attribute | Description |
	| --------- | ----------- |
	| State     | Date last subscribed activity  |
	| Last update   | Timestamp of last data refresh, throttled to limit data fetch to 1h |
  | last activity date  | Date last subscribed activity  |
  | last activity name  | Name of the last subscribed activity |
  | last activity group |  Group of the last subscribed activity  |
  | last activity link  | Link of the last subscribed activity   |
	
</details>

## Status
Still some optimisations are planned, see [Issues](https://github.com/myTselection/JNM/issues) section in GitHub.

## Technical pointers
The main logic and API connection related code can be found within source code JNM/custom_components/MyEnery:
- [sensor.py](https://github.com/myTselection/JNM/blob/master/custom_components/JNM/sensor.py)
- [utils.py](https://github.com/myTselection/JNM/blob/master/custom_components/JNM/utils.py) -> mainly ComponentSession class

All other files just contain boilerplat code for the integration to work wtihin HA or to have some constants/strings/translations.

If you would encounter some issues with this custom component, you can enable extra debug logging by adding below into your `configuration.yaml`:
<details><summary>Click to show example</summary>
	
```
logger:
  default: info
  logs:
     custom_components.jnm: debug
```
</details>

Since the sensors of this JNM integration may contain much data in the attributes, it might be desired to disable full detailed history logging in the recorder of Home Assistant. You may disable it by adding below in `configuration.yaml`:
```
recorder:
  exclude:
    entity_globs:
      - sensor.jnm*
```

## Example markdown
<details><summary>Below markdown can be used to display all upcoming activities</summary>

```
type: markdown
content: >-
  Volgende activiteit:
  {{states('sensor.jnm_[name]_next_activity')| as_timestamp |
  timestamp_custom("%a %d/%m/%Y")}} -
  [{{state_attr('sensor.jnm_[name]_next_activity','next
  activity
  name')}}]({{state_attr('sensor.jnm_[name]_next_activity','next
  activity link')}})

  {% if states('sensor.jnm_[name]_next_activity') ==
  states('sensor.jnm_[name]_last_subscribed_activity')
  %}Ingeschreven{% else %}**Nog niet ingeschreven**{% endif %}



  | Datum | Activiteit |

  | :-----| :----------|

  {% for activity in state_attr('sensor.jnm_[name]_next_activity','future activities') %}| {{activity.date| as_timestamp | timestamp_custom("%a%d/%m/%Y")}} | 
  {% if activity.details is defined %}<details><summary>[{{activity.name}}]({{activity.link}})</summary><table><tr><th>Locatie</th><td><a
  href="https://www.google.com/maps?q={{activity.details.location}}">{{activity.details.location}}</a></td></tr><tr><th>Uur</th><td>{{activity.details.start_time}}
  - {{activity.details.end_time}}</td></tr>{% if activity.details.activity_description is defined %}<tr><th>Omschrijving</th><td>{{activity.details.activity_description}}</td></tr>{% endif %}{% if activity.details.num_participants is defined %}<tr><th>Deelnemers</th><td>{{activity.details.num_participants}}{% if activity.details.subscribed_members is defined %}: {{activity.details.subscribed_members | join(' ')}}{% endif %}</td></tr>{% endif %}</table><details>{% else %}[{{activity.name}}]({{activity.link}}){% endif %} |

  {% endfor %}



  Laatst bijgewerkt
  {{state_attr('sensor.jnm_[name]_group','last update')|
  as_timestamp | timestamp_custom("%a %d/%m/%Y %H:%M")}}


```

</details>
