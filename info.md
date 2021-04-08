[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

# Govee BLE Home Assistant Component

A custom component for [Home Assistant][hass] that listens for the advertisement messages broadcast by Govee Bluetooth Low Energy devices.

## Supported Devices

- [Govee H5074][h5074]
- [Govee H5174][h5174]

**This component will set up the following platforms.**

| Platform | Description                                              |
| -------- | -------------------------------------------------------- |
| `sensor` | Show info about discovered Bluetooth Low Energy devices. |

![example][exampleimg]

{% if not installed %}

## Installation

1. Click install.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Govee BLE".

{% endif %}

## Configuration is done in the UI

<!---->

---

## Credits

This was originally based on/shamelessly copied/inspired from [Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci][goveetemp_bt_hci] and [irremotus/govee][govee]

---

[govee_ble]: https://github.com/natekspencer/hacs-govee_ble
[buymecoffee]: https://www.buymeacoffee.com/natekspencer
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/natekspencer/hacs-govee_ble.svg?style=for-the-badge
[commits]: https://github.com/natekspencer/hacs-govee_ble/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license]: https://github.com/natekspencer/hacs-govee_ble/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/natekspencer/hacs-govee_ble.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40natekspencer-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/natekspencer/hacs-govee_ble.svg?style=for-the-badge
[releases]: https://github.com/natekspencer/hacs-govee_ble/releases
[user_profile]: https://github.com/natekspencer
[hass]: https://www.home-assistant.io
[h5074]: https://www.amazon.com/Govee-Thermometer-Hygrometer-Bluetooth-Temperature/dp/B07R586J37
[h5174]: https://www.amazon.com/Govee-Bluetooth-Hygrometer-Thermometer-Greenhouse/dp/B08JLNXLVZ
[orgoveetemp_bt_hciigin]: https://github.com/Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci
[govee]: https://github.com/irremotus/govee
