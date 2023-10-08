[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/myTselection/JNM.svg)](https://github.com/myTselection/JNM/releases)
![GitHub repo size](https://img.shields.io/github/repo-size/myTselection/JNM.svg)

[![GitHub issues](https://img.shields.io/github/issues/myTselection/JNM.svg)](https://github.com/myTselection/JNM/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/myTselection/JNM.svg)](https://github.com/myTselection/JNM/commits/master)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/myTselection/JNM.svg)](https://github.com/myTselection/JNM/graphs/commit-activity)

# JNM - Home Assistant integration
[JNM](https://www.jnm.be/) Home Assistant custom component integration for Belgium. This custom component has been built from the ground up to bring jnm.be site data into Home Assistant sensors in order to follow up activities and subscribe. This integration is built against the public website provided by jnm.be for Belgium and has not been tested for any other countries.

This integration is in no way affiliated with JNM.

<p align="center"><img src="https://raw.githubusercontent.com/myTselection/JNM/master/icon.png"/></p>


## Installation
- [HACS](https://hacs.xyz/): add url https://github.com/myTselection/JNM as custom repository (HACS > Integration > option: Custom Repositories)
	- [![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=myTselection&repository=JNM&category=integration)

- Restart Home Assistant
- Add 'JNM' integration via HA Settings > 'Devices and Services' > 'Integrations'



## Integration
Device `JNM` should become available with the following sensors:
- <details><summary><code>JNM [username]</code> with details </summary>


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
