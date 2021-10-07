from __future__ import annotations

import abc
import asyncio
from asyncio.tasks import Task
import logging
from math import ceil
import platform
from struct import unpack_from
import traceback
from typing import Any, Callable, Dict, Optional, Type

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakDBusError, BleakError

from .attribute import Battery, Color, DeviceInfo, Hygrometer, Light, Mode, Thermometer
from .enums import MusicMode
from .helpers import (
    command_with_checksum,
    decode_temperature_and_humidity,
    get_govee_model,
    twos_complement,
)

_LOGGER = logging.getLogger(__name__)


class Device(abc.ABC):
    """Abstract device class."""

    SUPPORTED_MODELS: set[str] = None

    def __init__(
        self, device: BLEDevice, advertisement: Optional[AdvertisementData] = None
    ) -> None:
        """Initialize a device."""
        self._device = device
        self._model = get_govee_model(device.name)
        if advertisement:
            self.update(device, advertisement)

    @property
    def address(self) -> str:
        """Return the address of the device."""
        return self._device.address

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device.name

    @property
    def rssi(self) -> int:
        """Return the rssi of the device."""
        return self._device.rssi

    @property
    def model(self) -> Optional[str]:
        """Return the model of the device."""
        return self._model

    @abc.abstractstaticmethod
    def update(self, device: BLEDevice, advertisement: AdvertisementData) -> None:
        """Update the device info based on BLE advertisement data."""
        raise NotImplementedError()

    def update_device(self, device: BLEDevice) -> None:
        """Update the device."""
        if self._device != device:
            self._device = device

    @abc.abstractmethod
    def dict(self):
        """Returns a dictionary of device data."""
        raise NotImplementedError()

    def __repr__(self) -> str:
        """Return pertinent data about this device."""
        return str(self.dict())


class UnsupportedDevice(Device):
    """Represents an unsupported device."""


class ThermoHygrometer(Device, Thermometer, Hygrometer, Battery):
    """Abstract Govee Thermo-Hygrometer Sensor Device."""

    MANUFACTURER_DATA_KEY: int = None
    OFFSET: int = None
    NUMBER_OF_BYTES: int = None

    def dict(self) -> Dict[str, Any]:
        """Return pertinent data about this device."""
        return {
            "address": self.address,
            "name": self.name,
            "model": self.model,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "battery": self.battery,
        }

    def update(self, device: BLEDevice, advertisement: AdvertisementData) -> None:
        """Update the device data from an advertisement."""
        self.update_device(device)

        update_data = advertisement.manufacturer_data.get(self.MANUFACTURER_DATA_KEY)
        if update_data and len(update_data) >= self.OFFSET + self.NUMBER_OF_BYTES:
            self.parse(update_data)

    @abc.abstractmethod
    def parse(self, data: bytes) -> None:
        """Parse the data."""
        raise NotImplementedError()


class ThermoHygrometerPacked(ThermoHygrometer):
    """Govee Thermo-Hygrometer Sensor with packed data for Temperature and Humidity."""

    NUMBER_OF_BYTES = 5

    def parse(self, data: bytes) -> None:
        """Parse the data."""
        temp, hum, batt = unpack_from("<HHB", data, self.OFFSET)
        self._temperature = float(twos_complement(temp) / 100)
        self._humidity = float(hum / 100)
        self._battery = int(batt)


class H50TH(ThermoHygrometerPacked):
    """
    Govee H50XX Thermo-Hygrometer Sensor.

    Supported Models:
    - H5051
    - H5052
    - H5071
    - H5074
    """

    SUPPORTED_MODELS = {"H5051", "H5052", "H5071", "H5074"}
    MANUFACTURER_DATA_KEY = 60552  # EC88
    OFFSET = 1


class H5179(ThermoHygrometerPacked):
    """
    Govee H5179 Thermo-Hygrometer Sensor.

    Supported Models:
    - H5179
    """

    SUPPORTED_MODELS = {"H5179"}
    MANUFACTURER_DATA_KEY = 34817  # 8801
    OFFSET = 4


class ThermoHygrometerEncoded(ThermoHygrometer):
    """Govee Thermo-Hygrometer Sensor with combined data for Temperature and Humidity."""

    NUMBER_OF_BYTES = 4

    def parse(self, data: bytes) -> None:
        """Parse the data."""
        self._temperature, self._humidity = decode_temperature_and_humidity(
            data[self.OFFSET : self.OFFSET + 3]
        )
        self._battery = int(data[self.OFFSET + 3])


class H507TH(ThermoHygrometerEncoded):
    """
    Govee H5072/5 Thermo-Hygrometer Sensor.

    Supported Models:
    - H5072
    - H5075
    """

    SUPPORTED_MODELS = {"H5072", "H5075"}
    MANUFACTURER_DATA_KEY = 60552  # EC88
    OFFSET = 1


class H51TH(ThermoHygrometerEncoded):
    """
    Govee H51XX Thermo-Hygrometer Sensor.

    Supported Models:
    - H5101
    - H5102
    - H5174
    - H5177
    """

    SUPPORTED_MODELS = {"H5101", "H5102", "H5174", "H5177"}
    MANUFACTURER_DATA_KEY = 1  # 0001
    OFFSET = 2


class BasicLight(Device, Light, DeviceInfo):
    """Basic light with on/off and brightness controls."""

    KEEP_ALIVE_SECONDS = 4
    NOTIFY_UUID = "00010203-0405-0607-0809-0a0b0c0d2b10"
    WRITE_UUID = "00010203-0405-0607-0809-0a0b0c0d2b11"

    _GET_ = "aa"
    _WRITE_ = "33"

    _POWER_ = "01"
    _BRIGHTNESS_ = "04"
    _FIRMWARE_ = "06"
    _HARDWARE_ = "0703"
    _LIGHT_INFO_ = "0f"

    def __init__(
        self, device: BLEDevice, advertisement: Optional[AdvertisementData] = None
    ) -> None:
        """Initialize a device."""
        super().__init__(device=device, advertisement=advertisement)
        self._log_notifications = False
        self._client: BleakClient = None
        self._device_detail_requested = False
        self._keep_alive: bool = False
        self._keep_alive_task: Task = None
        self._connected_callback: Callable = None
        self._lights = 1
        self._custom_parser: dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        self._connect_task: asyncio.Task = None
        self.connection_attempt = 0

        self.GET_DEVICE_DETAIL_COMMANDS = {
            "FIRMWARE": self._get_command(self._FIRMWARE_),
            "HARDWARE": self._get_command(self._HARDWARE_),
            "LIGHTINFO": self._get_command(self._LIGHT_INFO_),
        }
        self.GET_STATE_COMMANDS = {
            "POWER": self._get_command(self._POWER_),
            "BRIGHTNESS": self._get_command(self._BRIGHTNESS_),
        }
        self.SET_COMMANDS = {
            "ON": self._write_command(self._POWER_ + "01"),
            "OFF": self._write_command(self._POWER_ + "00"),
        }
        self.ALL_COMMANDS = (
            self.GET_DEVICE_DETAIL_COMMANDS
            | self.GET_STATE_COMMANDS
            | self.SET_COMMANDS
        )

    def _get_command(self, command):
        """Construct a get command."""
        return command_with_checksum(self._GET_ + command)

    def _write_command(self, command):
        """Construct a write command."""
        return command_with_checksum(self._WRITE_ + command)

    def update(self, device: BLEDevice, advertisement: AdvertisementData):
        """Update the device data from an advertisement."""
        return

    def dict(self):
        return {
            "address": self.address,
            "name": self.name,
            "model": self.model,
            "is_on": self.is_on,
            "brightness": self.brightness,
            "firmware": self.firmware,
            "hardware": self.hardware,
        }

    def parse(self, _: int, data: bytearray) -> None:
        """Parse the data."""
        unknown = False

        hex_data = data.hex()
        if hex_data.startswith(self._GET_):

            def is_type(type: str) -> bool:
                """Returns True if data is of `type`."""
                return hex_data[len(self._GET_) :].startswith(type)

            parse_method = next(
                (value for key, value in self._custom_parser.items() if is_type(key)),
                None,
            )
            if parse_method:
                parse_method(data)

            else:
                if is_type(self._POWER_):
                    self._is_on = unpack_from("?", data, 2)[0]

                elif is_type(self._BRIGHTNESS_):
                    self._brightness = unpack_from("B", data, 2)[0]

                elif is_type(self._FIRMWARE_):
                    self._firmware = data[2:9].decode("utf-8")

                elif is_type(self._HARDWARE_):
                    index = int(len(self._GET_ + self._HARDWARE_) / 2)
                    self._hardware = data[index : index + 7].decode("utf-8")

                elif is_type(self._LIGHT_INFO_):
                    self.parse_light_info(data)

                else:
                    unknown = True

        elif not hex_data.startswith(self._WRITE_):
            unknown = True

        if unknown or self._log_notifications:
            _LOGGER.debug(
                "%sotification from %s - %s",
                ("Unknown n" if unknown else "N"),
                self._device,
                hex_data,
            )

    def add_custom_type_parser(self, type: str, parser: Callable) -> None:
        """Add a custom type parser."""
        self._custom_parser[type] = parser

    def parse_light_info(self, data: bytearray) -> None:
        """Parse light info."""
        self._lights = unpack_from("B", data, 2)[0]

    def register_connected_callback(self, callback: Callable) -> None:
        """Register a callback that is called when successfully connected."""
        self._connected_callback = callback

    async def _attempt_connection(self) -> bool:
        """Attempt to establish a connection to the device."""
        self.connection_attempt += 1

        if platform.system() == "Darwin":
            # macOS BLE device services aren't properly reset on reconnection
            # attempts as of bleak==0.12.1, so we create a new client instead
            self._client = BleakClient(self.address)
        elif not self._client:
            self._client = BleakClient(self._device)

        for _ in range(10):
            try:
                await self._client.connect(timeout=30)
                await self._client.start_notify(self.NOTIFY_UUID, self.parse)

                if self._keep_alive:
                    asyncio.create_task(self.__keep_alive())

                # sleep so notifications are received properly
                await asyncio.sleep(0.25)

                _LOGGER.debug("Connected to %s", self._device)

                if self._connected_callback:
                    self._connected_callback()

                if not self._device_detail_requested:
                    asyncio.create_task(self.request_device_details())

                return True
            except BleakDBusError as ex:
                # Allow "Software caused connection abort" and "Disconnected early" errors from bluez to retry attempt
                if not (
                    ex.dbus_error == "org.bluez.Error.Failed"
                    and ex.dbus_error_details
                    in ("Software caused connection abort", "Disconnected early")
                ):
                    _LOGGER.error(
                        "BleakDBusError occurred while connecting to device %s: %s",
                        self._device,
                        ex,
                    )
                    return False
            except (BleakError, TypeError) as ex:
                _LOGGER.error(
                    "%s occurred while connecting to device %s - %s",
                    type(ex).__name__,
                    self._device,
                    ex,
                )
                return False
            except asyncio.TimeoutError:
                _LOGGER.debug(
                    "TimeoutError occurred while connecting to device %s", self._device
                )
                return False
            except asyncio.InvalidStateError as ex:
                _LOGGER.error(
                    "InvalidStateError occurred while connecting to device %s - %s",
                    self._device,
                    ex,
                )
                return False

    async def _request_connection(self) -> bool:
        """Request a connection to the device."""
        if self.is_connected:
            return True

        async with self._lock:
            if not self._connect_task or self._connect_task.done():
                self._connect_task = asyncio.create_task(self._attempt_connection())

        connected = False
        try:
            connected = await asyncio.wait_for(self._connect_task, 60)
        except asyncio.TimeoutError:
            _LOGGER.debug("TimeoutError waiting on %s's connect task", self._device)
        except asyncio.InvalidStateError as ex:
            _LOGGER.debug(
                "InvalidStateError waiting on %s's connect task - %s", self._device, ex
            )
        finally:
            if connected:
                self.connection_attempt = 0
            return connected

    async def connect(self, keep_alive: bool = False) -> bool:
        """Connect to the device."""
        self._keep_alive = keep_alive

        if self.is_connected:
            return True

        return await self._request_connection()

    @property
    def is_connected(self) -> bool:
        """Returns whether the device is currently connected."""
        return bool(self._client and self._client.is_connected)

    async def request_device_details(self) -> None:
        """Request device details."""
        self._device_detail_requested = True
        for command in list(self.GET_DEVICE_DETAIL_COMMANDS.values()):
            self._device_detail_requested &= await self._send_command(command)
        await self.request_update()

    async def disconnect(self) -> bool:
        """Disconnect from the device."""
        async with self._lock:
            self._keep_alive = False

            await self.__cancel_connect_task()
            if self.is_connected:
                await self._client.disconnect()
            await self.__cancel_keep_alive_task()

            _LOGGER.debug("Disconnected from %s", self._device)
        return True

    async def __cancel_connect_task(self) -> None:
        """Cancel the connect task."""
        if self._connect_task:
            self._connect_task.cancel()
            try:
                await self._connect_task
            except asyncio.CancelledError:
                pass
            finally:
                self._connect_task = None

    async def __keep_alive(self) -> None:
        """Keep the connection to the device alive."""

        async def keep_alive():
            """Keep alive loop."""
            while self._keep_alive and self.is_connected:
                await asyncio.sleep(self.KEEP_ALIVE_SECONDS)
                await self._send_command("POWER")

        await self.__cancel_keep_alive_task()
        self._keep_alive_task = asyncio.create_task(keep_alive())

    async def __cancel_keep_alive_task(self) -> None:
        """Cancel the keep alive task."""
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass
            finally:
                self._keep_alive_task = None

    async def request_update(self, disconnect: bool = False) -> None:
        """Write commands to the device to request updated data."""
        for command in list(self.GET_STATE_COMMANDS.values()):
            await self._send_command(command)
        if disconnect:
            await self.disconnect()

    async def _send_command(self, command: str | bytes) -> bool:
        """Write a get command to the device."""
        if isinstance(command, str):
            command = (
                bytes.fromhex(command)
                if len(command) == 40
                else self.ALL_COMMANDS[command]
            )
        if await self._request_connection() and self.WRITE_UUID in [
            characteristic.uuid
            for characteristic in list(self._client.services.characteristics.values())
        ]:
            try:
                await self._client.write_gatt_char(self.WRITE_UUID, command)
                await asyncio.sleep(0.1)
                return True
            except BleakDBusError as ex:
                if (
                    ex.dbus_error == "org.bluez.Error.Failed"
                    and ex.dbus_error_details == "Not connected"
                ):
                    _LOGGER.warning(
                        "Connection was lost while trying to send command to %s",
                        self._device,
                    )
                else:
                    _LOGGER.error(
                        "Error sending command to %s - %s",
                        self._device,
                        ex,
                    )
        return False

    async def turn_on(self) -> None:
        """Turns on the light."""
        if await self._send_command("ON"):
            self._is_on = True

    async def turn_off(self) -> None:
        """Turns off the light."""
        if await self._send_command("OFF"):
            self._is_on = False

    async def set_brightness(self, brightness: int) -> None:
        """Set the brightness of the light."""
        brightness = self._brightness_scaled(brightness, True)
        command = self._write_command(f"{self._BRIGHTNESS_}{brightness:02x}")
        if await self._send_command(command):
            self._brightness = brightness

        # setting the brightness on a light will turn it on, but the power state bit
        # doesn't get updated unless an explicit call to turn on the device is sent
        if not self.is_on:
            await self.turn_on()


class MulticoloredLight(BasicLight, Color, Mode):
    """Govee Multicolored Lights."""

    _COLOR_ = "05"
    MODES = {}
    SCENES = {}

    def __init__(
        self, device: BLEDevice, advertisement: Optional[AdvertisementData] = None
    ) -> None:
        """Initialize a device."""
        super().__init__(device=device, advertisement=advertisement)

        color_command = {
            "COLOR": self._get_command(self._COLOR_),
        }
        self.GET_STATE_COMMANDS.update(color_command)
        self.ALL_COMMANDS.update(color_command)

        self.add_custom_type_parser(self._COLOR_, self.parse_color)

    def parse_color(self, data: bytearray) -> None:
        self._mode = unpack_from("B", data, 2)[0]

        if self.mode == self.MODES.get("Music", None):
            self._music_mode = MusicMode(unpack_from("B", data, 3)[0])
            if self.music_mode in [MusicMode.SPECTRUM, MusicMode.ROLLING]:
                self._rgb_color = unpack_from("BBB", data, 5)
            # Set other color values to none
            self._scene = None

        elif self.mode == self.MODES.get("Color", None):
            if unpack_from("?", data, 6)[0]:
                self._rgb_color = unpack_from("BBB", data, 7)
                if self._rgb_color == (0, 0, 0):
                    self._rgb_color = unpack_from("BBB", data, 3)
            else:
                self._rgb_color = unpack_from("BBB", data, 3)
            # Set other color values to none
            self._music_mode = None
            self._scene = None

        elif self.mode == self.MODES.get("Scene", None):
            self._scene = unpack_from("B", data, 3)[0]
            # Set other color values to none
            self._music_mode = None

        elif self.mode == self.MODES.get("Segment", None):
            self._music_mode = None
            self._scene = None

    async def set_color(self, rgb_color: tuple) -> None:
        """Set the color of the light."""
        command = self._write_command(
            f"{self._COLOR_}{self.MODES['Color']:02x}{'%02x%02x%02x' % rgb_color}"
        )
        if await self._send_command(command):
            self._rgb_color = rgb_color

    async def set_scene(self, scene_name: str, **kwargs):
        """Set the scene based on the name."""
        scene_number = self.SCENES[scene_name]
        command = self._write_command(
            f"{self._COLOR_}{self.MODES['Scene']:02x}{scene_number:02x}"
        )
        if await self._send_command(command):
            self._scene = scene_number


class Lightstrip(MulticoloredLight):
    """
    Govee lightstrips.

    Supported Models:
    - H6163
    """

    SUPPORTED_MODELS = {"H6163"}
    MODES = {"Music": 1, "Color": 2, "Scene": 4, "DIY": 10, "Segment": 11}
    SCENES = {
        "Sunrise": 0,
        "Sunset": 1,
        "Movie": 4,
        "Dating": 5,
        "Romantic": 7,
        "Twinkle": 8,
        "Candlelight": 9,
        "Snow Flake": 15,
    }


class StringLight(MulticoloredLight):
    """
    Govee string lights.

    Supported Models:
    - H7002
    """

    SUPPORTED_MODELS: set[str] = {"H7002"}
    BULB_COUNT: int = 15
    MODES = {"Scene": 9, "Segment": 11}
    SCENES = {
        "Illumination": 1,
        "Gradient": 2,
        "Raindrop": 3,
        "Colorful": 4,
        "Marquee": 5,
        "Blink": 6,
        "Snow Flake": 7,
        "Starry Sky": 8,
    }
    SCENE_COLORS_MAX = 12

    _BULB_STATE_ = "a2"
    _WRITE_SCENE_ = "a101"

    def __init__(
        self, device: BLEDevice, advertisement: Optional[AdvertisementData] = None
    ) -> None:
        """Initialize a cafe light."""
        super().__init__(device=device, advertisement=advertisement)

        self._brightness_scale = 100
        self._bulbs: list[tuple[int, int, int]] = []

        self.add_custom_type_parser(self._BULB_STATE_, self.parse_bulb_state)

        def ignore(_: bytearray) -> None:
            """Don't do anything."""

        self.add_custom_type_parser(self._WRITE_SCENE_, ignore)

    def parse_light_info(self, data: bytearray) -> None:
        """Parse light info."""
        super().parse_light_info(data)
        bulb_state_commands = {
            f"BULB_STATE_{i}": self._get_command(f"{self._BULB_STATE_}{i:02x}")
            for i in range(1, ceil(self.BULB_COUNT * self._lights / 4) + 1)
        }
        self.GET_STATE_COMMANDS.update(bulb_state_commands)
        self.ALL_COMMANDS.update(bulb_state_commands)

    def parse_bulb_state(self, data: bytearray) -> None:
        """Parse bulb state."""
        bulb_set = unpack_from("B", data, 2)[0]
        bulb_data = list(zip(*[iter(unpack_from("B" * 12, data, 3))] * 3))
        self._bulbs[(bulb_set - 1) * 4 : bulb_set * 4] = bulb_data
        if bulb_set == 1:
            self._rgb_color = bulb_data[0]

    @property
    def number_of_bulbs(self) -> int:
        """Return the number of bulbs."""
        return self._lights * self.BULB_COUNT

    @property
    def bulbs(self) -> list[tuple[int, int, int]]:
        """Return info about the bulbs."""
        return self._bulbs[0 : self.number_of_bulbs]

    async def set_color(self, rgb_color: tuple):
        """Set the color of the light."""
        command = self._write_command(
            f"{self._COLOR_}0b{'%02x%02x%02x' % rgb_color}{'f'*ceil(self.number_of_bulbs/4)}"
        )
        if await self._send_command(command):
            self._rgb_color = rgb_color

    async def set_scene(
        self,
        scene_name: str,
        speed_percentage: int = 50,
        color_list: list[tuple[int, int, int]] = [
            (0xFF, 0x00, 0x00),
            (0x00, 0x00, 0xFF),
            (0xFF, 0xFF, 0x00),
            (0x00, 0xFF, 0x00),
        ],
    ) -> None:
        """Set the scene for the device."""
        scene_number = self.SCENES[scene_name]
        color_count = len(color_list)
        if color_count > self.SCENE_COLORS_MAX:
            _LOGGER.warning(
                "The number of colors provided exceeds the maximum allowed - only the first %s colors will be used for the custom scene on %s",
                self.SCENE_COLORS_MAX,
                self._device,
            )

        START_PACKET, FIRST_PACKET, END_PACKET = "00", "01", "ff"

        packet_count = 1 if color_count < 4 else (2 if color_count < 10 else 3)
        color_code_str = "".join("%02x%02x%02x" % color for color in color_list[:12])

        commands = [
            command_with_checksum(
                f"{self._WRITE_SCENE_}{START_PACKET}{packet_count:02x}"
            )
        ]
        commands.append(
            command_with_checksum(
                f"{self._WRITE_SCENE_}{FIRST_PACKET}{scene_number:02x}0700{min(speed_percentage,100):02x}{color_count*3:02x}{color_code_str[:22]}"
            )
        )
        commands.extend(
            command_with_checksum(
                f"{self._WRITE_SCENE_}{i:02x}{color_code_str[(i-2)*32+22:][:32]}"
            )
            for i in range(2, packet_count + 1)
        )
        commands.append(command_with_checksum(f"{self._WRITE_SCENE_}{END_PACKET}"))
        for command in commands:
            if not await self._send_command(command):
                return
        self._scene = scene_number


VALID_CLASSES: set[Type[Device]] = {
    H50TH,
    H507TH,
    H51TH,
    H5179,
    Lightstrip,
    StringLight,
}
MODEL_MAP = {model: cls for cls in VALID_CLASSES for model in cls.SUPPORTED_MODELS}


def determine_known_device(
    device: BLEDevice, advertisement: Optional[AdvertisementData] = None
) -> Optional[Device]:
    """Determine if the advertisement data is of a known device."""
    model = get_govee_model(device.name)
    if model in MODEL_MAP:
        return MODEL_MAP[model](device, advertisement)
    elif model and advertisement.manufacturer_data:
        _LOGGER.debug(
            "%s appears to be a Govee %s, but no handler has been created. Consider opening an issue at https://github.com/natekspencer/hacs-govee_ble/issues with the advertisement message from above.",
            device.name,
            model,
        )
    return None
