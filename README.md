# Govee BLE Home Assistant Component

Home Assistant integration for a Govee Bluetooth Low Energy (BLE) devices.

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

**This component will set up the following platforms.**

| Platform | Description                                                                                                              |
| -------- | ------------------------------------------------------------------------------------------------------------------------ |
| `sensor` | Show info about discovered Bluetooth Low Energy devices including Bluetooth Address, Temperature, Humidity, and Battery. |

![example][exampleimg]

## Installation

There are two main ways to install this custom component within your Home Assistant instance:

1. Using [HACS] (see https://hacs.xyz/ for installation instructions if you do not already have it installed):

   1. From within Home Assistant, click on the link to **HACS**
   2. Click on **Integrations**
   3. Click on the vertical ellipsis in the top right and select **Custom repositories**
   4. Enter the URL for this repository in the section that says _Add custom repository URL_ and select **Integration** in the _Category_ dropdown list
   5. Click the **ADD** button
   6. Close the _Custom repositories_ window
   7. You should now be able to see the _Govee BLE_ card on the HACS Integrations page. Click on **INSTALL** and proceed with the installation instructions.
   8. Restart your Home Assistant instance and then proceed to the _Configuration_ section below.

2. Manual Installation:
   1. Download or clone this repository
   2. Copy the contents of the folder **custom_components/govee_ble** into the same file structure on your Home Assistant instance
      - An easy way to do this is using the [Samba add-on](https://www.home-assistant.io/getting-started/configuration/#editing-configuration-via-sambawindows-networking), but feel free to do so however you want
   3. Restart your Home Assistant instance and then proceed to the _Configuration_ section below.

While the manual installation above seems like less steps, it's important to note that you will not be able to see updates to this custom component unless you are subscribed to the watch list. You will then have to repeat each step in the process. By using HACS, you'll be able to see that an update is available and easily update the custom component.

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

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
