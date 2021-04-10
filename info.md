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

## Supported Govee Devices

- [H5051][h5051]
- H5052
- H5053
- [H5071][h5071]
- [H5072][h5072]
- [H5074][h5074]
- [H5075][h5075]
- [H5101][h5101]
- [H5102][h5102]
- [H5174][h5174]
- [H5177][h5177]
- [H5179][h5179]

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

## Credits

This was originally based on/shamelessly copied/inspired from [Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci][goveetemp_bt_hci] and [irremotus/govee][govee]. These, as well as [asednev][govee-bt-client], were incredibly valuable resources for identifying packet data for sensors I don't own myself.

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
[//]: #
[//]: # "Credits"
[//]: #
[goveetemp_bt_hci]: https://github.com/Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci
[govee]: https://github.com/irremotus/govee
[govee-bt-client]: https://github.com/asednev/govee-bt-client
[//]: #
[//]: # "Device links"
[//]: #
[h5051]: https://www.amazon.com/dp/B07FBCTQ3L
[h5071]: https://www.amazon.com/dp/B07TWMSNH5
[h5072]: https://www.amazon.com/dp/B07DWMJKP5
[h5074]: https://www.amazon.com/dp/B07R586J37
[h5075]: https://www.amazon.com/dp/B0872X4H4J
[h5101]: https://www.amazon.com/dp/B08CGM8DC7
[h5102]: https://www.amazon.com/dp/B087313N8F
[h5174]: https://www.amazon.com/dp/B08JLNXLVZ
[h5177]: https://www.amazon.com/dp/B08C9VYMHY
[h5179]: https://www.amazon.com/dp/B0872ZWV8X
