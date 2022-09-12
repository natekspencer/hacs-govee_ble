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

## Supported Govee Devices

- [H5051][h5051]
- H5052
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
   8. Restart your Home Assistant instance and then proceed to the [_Configuration_](#configuration) section below.

2. Manual Installation:
   1. Download or clone this repository
   2. Copy the contents of the folder **custom_components/govee_ble** into the same file structure on your Home Assistant instance
      - An easy way to do this is using the [Samba add-on](https://www.home-assistant.io/getting-started/configuration/#editing-configuration-via-sambawindows-networking), but feel free to do so however you want
   3. Restart your Home Assistant instance and then proceed to the [_Configuration_](#configuration) section below.

While the manual installation above seems like less steps, it's important to note that you will not be able to see updates to this custom component unless you are subscribed to the watch list. You will then have to repeat each step in the process. By using HACS, you'll be able to see that an update is available and easily update the custom component.

## Configuration

There is a config flow for this integration. After installing the custom component and restarting Home Assistant:

1. Go to **Configuration** -> **Integrations**
2. Click **+ ADD INTEGRATION** to setup a new integration
3. Search for **Govee BLE** and click on it
4. You will be guided through the rest of the setup process via the config flow

## Debugging

If one of your sensors is reporting incorrectly or you have a sensor that isn't showing up at all, you can enable debugging on the custom component by utilizing Home Assistant's built-in [logger][hass_logger]. Just add the following entry under the `logs` section in your `configuration.yaml` file:

```yaml
custom_components.govee_ble: debug
```

After restarting Home Assistant, go to the [logs][my_hass_logs], watch the output and consider [opening a new issue on GitHub](../../issues/new). Make sure you search for [open issues](../../issues) before reporting, just in case someone else has already encountered it.

Because of the number of Bluetooth devices that may be within range and to limit the number of log entries, only devices that advertise their name and start with **ihoment\_**, **Govee\_**, **Minger\_**, **GBK\_** or **GVH** will be logged. This is the same way the Govee app currently determines supported devices, so it may change as new devices are released. If you have a Govee device that doesn't match this pattern, please [open an issue on GitHub](../../issues/new) and include the name of your Govee device that is being advertised so it can be added to the logic.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

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
[hass_logger]: https://www.home-assistant.io/integrations/logger/
[my_hass_logs]: https://my.home-assistant.io/redirect/logs/
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
