from __future__ import annotations

import sys
import time
import warnings
from importlib.metadata import version
from typing import Callable

from blinkstick.colors import (
    hex_to_rgb,
    name_to_rgb,
    remap_color,
    remap_rgb_value,
    remap_rgb_value_reverse,
    ColorFormat,
)
from blinkstick.constants import VENDOR_ID, PRODUCT_ID, BlinkStickVariant
from blinkstick.exceptions import BlinkStickException
from blinkstick.utilities import string_to_info_block_data

if sys.platform == "win32":
    from blinkstick.backends.win32 import Win32Backend as USBBackend
    import pywinusb.hid as hid  # type: ignore
else:
    from blinkstick.backends.unix_like import UnixLikeBackend as USBBackend
    import usb.core  # type: ignore
    import usb.util  # type: ignore

from random import randint

"""
Main module to control BlinkStick and BlinkStick Pro devices.
"""


class BlinkStick:
    """
    BlinkStick class is designed to control regular BlinkStick devices, or BlinkStick Pro
    devices in Normal or Inverse modes. Please refer to :meth:`BlinkStick.set_mode` for more details
    about BlinkStick Pro backend modes.

    Code examples on how you can use this class are available here:

    https://github.com/arvydas/blinkstick-python/wiki
    """

    inverse: bool
    error_reporting = True
    max_rgb_value: int

    backend: USBBackend
    bs_serial: str

    def __init__(self, device=None, error_reporting: bool = True):
        """Constructor for the class.

        :param error_reporting: display errors if they occur during
            communication with the backend
        :type error_reporting: Boolean
        """
        self.error_reporting = error_reporting
        self.max_rgb_value = 255
        self.inverse = False

        if device:
            self.backend = USBBackend(device)
            self.bs_serial = self.get_serial()

    def get_serial(self) -> str:
        """Returns the serial number of the BlinkStick device.

        ::

           BSnnnnnn-1.0
           ||  |    | |- Software minor version
           ||  |    |--- Software major version
           ||  |-------- Denotes sequential number
           ||----------- Denotes BlinkStick backend

        Software version defines the capabilities of the backend

        :returns: Blinkstick device serial number
        :rtype: str
        """
        return self.backend.get_serial()

    def get_manufacturer(self) -> str:
        """Get the device manufacturer's name.

        :returns: Device manufacturer's name
        :rtype: str
        """
        return self.backend.get_manufacturer()

    def get_variant(self) -> BlinkStickVariant:
        """Get the product variant of the backend.

        :returns: An enum representing the variant of BlinkStick device
        :rtype: BlinkStickVariant
        """

        serial = self.get_serial()
        major = serial[-3]

        version_attribute = self.backend.get_version_attribute()

        return BlinkStickVariant.identify(int(major), version_attribute)

    def get_variant_string(self) -> str:
        """Get the product variant of the backend as string.

        :returns: String representation of the BlinkStickVariant enum e.g. "BlinkStick", "BlinkStick Pro", etc
        :rtype: string
        """
        return self.get_variant().description

    def get_description(self) -> str:
        """Get the device description.

        :returns: Device description
        :rtype: str
        """
        return self.backend.get_description()

    def set_error_reporting(self, error_reporting: bool) -> None:
        """Enable or disable error reporting

        :param error_reporting: display errors if they occur during
            communication with the backend
        :type error_reporting: Boolean
        """
        self.error_reporting = error_reporting

    def set_color(
        self,
        channel: int = 0,
        index: int = 0,
        red: int = 0,
        green: int = 0,
        blue: int = 0,
        name: str | None = None,
        hex: str | None = None,
    ) -> None:
        """Set the color to the backend as RGB

        :param channel: the channel which to send data to (R=0, G=1,
            B=2)
        :type channel: int
        :param index: the index of the LED
        :type index: int
        :param red: Red color intensity 0 is off, 255 is full red
            intensity
        :type red: int
        :param green: Green color intensity 0 is off, 255 is full green
            intensity
        :type green: int
        :param blue: Blue color intensity 0 is off, 255 is full blue
            intensity
        :type blue: int
        :param name: Use CSS color name as defined here: http://www.w3.org/TR/css3-color/
        :type name: str | None
        :param hex: Specify color using hexadecimal color value e.g.
            '#FF3366'
        :type hex: str | None
        """

        red, green, blue = self._determine_rgb(
            red=red, green=green, blue=blue, name=name, hex=hex
        )

        r = int(round(red, 3))
        g = int(round(green, 3))
        b = int(round(blue, 3))

        if self.inverse:
            r, g, b = 255 - r, 255 - g, 255 - b

        if index == 0 and channel == 0:
            control_string = bytes(bytearray([0, r, g, b]))
            report_id = 0x0001
        else:
            control_string = bytes(bytearray([5, channel, index, r, g, b]))
            report_id = 0x0005

        if self.error_reporting:
            self.backend.control_transfer(0x20, 0x9, report_id, 0, control_string)
        else:
            try:
                self.backend.control_transfer(0x20, 0x9, report_id, 0, control_string)
            except Exception:
                pass

    def _determine_rgb(
        self,
        red: int = 0,
        green: int = 0,
        blue: int = 0,
        name: str | None = None,
        hex: str | None = None,
    ) -> tuple[int, int, int]:

        try:
            if name:
                # Special case for name="random"
                if name == "random":
                    red = randint(0, 255)
                    green = randint(0, 255)
                    blue = randint(0, 255)
                else:
                    red, green, blue = name_to_rgb(name)
            elif hex:
                red, green, blue = hex_to_rgb(hex)
        except ValueError:
            red = green = blue = 0

        red, green, blue = remap_rgb_value((red, green, blue), self.max_rgb_value)

        # TODO - do smarts to determine input type from red var in case it is not int

        return red, green, blue

    def _get_color_rgb(self, index: int = 0) -> tuple[int, int, int]:
        if index == 0:
            device_bytes = self.backend.control_transfer(
                0x80 | 0x20, 0x1, 0x0001, 0, 33
            )
            if self.inverse:
                return (
                    255 - device_bytes[1],
                    255 - device_bytes[2],
                    255 - device_bytes[3],
                )
            else:
                return device_bytes[1], device_bytes[2], device_bytes[3]
        else:
            data = self.get_led_data((index + 1) * 3)

            return data[index * 3 + 1], data[index * 3], data[index * 3 + 2]

    def _get_color_hex(self, index: int = 0) -> str:
        r, g, b = self._get_color_rgb(index)
        return "#%02x%02x%02x" % (r, g, b)

    def get_color(
        self,
        index: int = 0,
        color_mode: ColorFormat = ColorFormat.RGB,
        color_format: str | None = None,
    ) -> tuple[int, int, int] | str:
        """Get the current backend color in the defined format.

        Currently supported formats:

            1. rgb (default) - Returns values as 3-tuple (r,g,b)
            2. hex - returns current backend color as hexadecimal string

        .. code-block:: python

           >>> b = blinkstick.find_first()
           >>> b.set_color(red=255,green=0,blue=0)
           >>> (r,g,b) = b.get_color() # Get color as rbg tuple
           (255,0,0)
           >>> hex = b.get_color(color_mode=ColorFormat.HEX) # Get color as hex string
           '#ff0000'

        :param index: the index of the LED
        :type index: int
        :param color_mode: the format to return the color in
            (ColorFormat.RGB or ColorFormat.HEX) - defaults to
            ColorFormat.RGB
        :type color_mode: ColorFormat
        :param color_format: "rgb" or "hex". Defaults to "rgb".
            Deprecated, use color_mode instead.
        :type color_format: str

        :returns: Either 3-tuple for R, G and B values, or hex string
        :rtype: (int, int, int) or str
        """
        # color_format is deprecated, and color_mode should be used instead
        # if color_format is specified, then raise a DeprecationWarning, but attempt to convert it to a ColorFormat enum
        # if it's not possible, then default to ColorFormat.RGB, in line with the previous behavior
        if color_format:
            warnings.warn(
                "color_format is deprecated, please use color_mode instead",
                DeprecationWarning,
            )
            try:
                color_mode = ColorFormat.from_name(color_format)
            except ValueError:
                color_mode = ColorFormat.RGB

        color_funcs: dict[ColorFormat, Callable[[int], tuple[int, int, int] | str]] = {
            ColorFormat.RGB: self._get_color_rgb,
            ColorFormat.HEX: self._get_color_hex,
        }

        return color_funcs.get(color_mode, self._get_color_rgb)(index)

    def _determine_report_id(self, led_count: int) -> tuple[int, int]:
        report_id = 9
        max_leds = 64

        if led_count <= 8 * 3:
            max_leds = 8
            report_id = 6
        elif led_count <= 16 * 3:
            max_leds = 16
            report_id = 7
        elif led_count <= 32 * 3:
            max_leds = 32
            report_id = 8
        elif led_count <= 64 * 3:
            max_leds = 64
            report_id = 9

        return report_id, max_leds

    def set_led_data(self, channel: int, data: list[int]) -> None:
        """Send LED data frame.

        :param channel: the channel which to send data to (R=0, G=1,
            B=2)
        :type channel: int
        :param data: The LED data frame in GRB color_mode
        :type data: list[int]
        """

        report_id, max_leds = self._determine_report_id(len(data))

        report = [0, channel]

        for i in range(0, max_leds * 3):
            if len(data) > i:
                report.append(data[i])
            else:
                report.append(0)

        self.backend.control_transfer(0x20, 0x9, report_id, 0, bytes(bytearray(report)))

    def get_led_data(self, count: int) -> list[int]:
        """Get LED data frame from the device.

        :param count: How much data to retrieve. Can be in the range of
            0..64*3
        :type count: int
        :returns: LED data currently stored in the RAM of the device
        :rtype: list[int]
        """

        report_id, max_leds = self._determine_report_id(count)

        device_bytes = self.backend.control_transfer(
            0x80 | 0x20, 0x1, report_id, 0, max_leds * 3 + 2
        )

        return device_bytes[2 : 2 + count * 3]

    def set_mode(self, mode: int) -> None:
        """Set backend mode for BlinkStick Pro. Device currently supports the following modes:

            - 0 - (default) use R, G and B channels to control single RGB LED
            - 1 - same as 0, but inverse mode
            - 2 - control up to 64 WS2812 individual LEDs per each R, G and B channel

        You can find out more about BlinkStick Pro modes:

        http://www.blinkstick.com/help/tutorials/blinkstick-pro-modes

        :param mode: Device mode to set
        :type mode: int
        """
        control_string = bytes(bytearray([4, mode]))

        self.backend.control_transfer(0x20, 0x9, 0x0004, 0, control_string)

    def get_mode(self) -> int:
        """Get BlinkStick Pro mode. Device currently supports the following modes:

            - 0 - (default) use R, G and B channels to control single RGB LED
            - 1 - same as 0, but inverse mode
            - 2 - control up to 64 WS2812 individual LEDs per each R, G and B channel

        You can find out more about BlinkStick Pro modes:

        http://www.blinkstick.com/help/tutorials/blinkstick-pro-modes

        :returns: Integer representing the current mode. -1 if not supported.
        :rtype: int
        """

        device_bytes = self.backend.control_transfer(0x80 | 0x20, 0x1, 0x0004, 0, 2)

        if len(device_bytes) >= 2:
            return device_bytes[1]
        else:
            return -1

    def set_led_count(self, count: int) -> None:
        """Set number of LEDs for supported devices

        :param count: number of LEDs to control
        :type count: int
        """
        control_string = bytes(bytearray([0x81, count]))

        self.backend.control_transfer(0x20, 0x9, 0x81, 0, control_string)

    def get_led_count(self) -> int:
        """Get number of LEDs for supported devices

        :returns: Number of LEDs
        :rtype: int
        """

        device_bytes = self.backend.control_transfer(0x80 | 0x20, 0x1, 0x81, 0, 2)

        if len(device_bytes) >= 2:
            return device_bytes[1]
        else:
            return -1

    def get_info_block1(self) -> str:
        """Get the contents of infoblock1 from the device.

        This is a 32 byte array that can contain any data. It's commonly used to
        hold the "Name" of the device making it easier to identify rather than
        a serial number.

        :returns: InfoBlock1 currently stored on the device
        :rtype: str
        """

        device_bytes = self.backend.control_transfer(0x80 | 0x20, 0x1, 0x0002, 0, 33)
        result = ""
        for i in device_bytes[1:]:
            if i == 0:
                break
            result += chr(i)
        return result

    def get_info_block2(self) -> str:
        """Get the contents of infoblock2 from the device.

        This is a 32 byte array that can contain any data.

        :returns: InfoBlock2 ntly stored on the device
        :rtype: str
        """
        device_bytes = self.backend.control_transfer(0x80 | 0x20, 0x1, 0x0003, 0, 33)
        result = ""
        for i in device_bytes[1:]:
            if i == 0:
                break
            result += chr(i)
        return result

    def set_info_block1(self, data: str) -> None:
        """Sets the infoblock1 with specified string.

        The content of infoblock1 will be set to the specified string. The rest of the 32 bytes will be filled with zeros.
        If the string is longer than 32 bytes, it will be truncated.

        :param data: Content to set in infoblock1
        :type data: str
        """
        self.backend.control_transfer(
            0x20, 0x9, 0x0002, 0, string_to_info_block_data(data)
        )

    def set_info_block2(self, data: str) -> None:
        """Sets the infoblock2 with specified string.

        The content of infoblock1 will be set to the specified string. The rest of the 32 bytes will be filled with zeros.
        If the string is longer than 32 bytes, it will be truncated.

        :param data: Content to set in infoblock2
        :type data: str
        """
        self.backend.control_transfer(
            0x20, 0x9, 0x0003, 0, string_to_info_block_data(data)
        )

    def set_random_color(self) -> None:
        """Sets the color of the device to a random value."""
        self.set_color(name="random")

    def turn_off(self) -> None:
        """Turns off the device LED. This is equivalent to setting the color to black."""
        self.set_color()

    def pulse(
        self,
        channel: int = 0,
        index: int = 0,
        red: int = 0,
        green: int = 0,
        blue: int = 0,
        name: str | None = None,
        hex: str | None = None,
        repeats: int = 1,
        duration: int = 1000,
        steps: int = 50,
    ) -> None:
        """Morph to the specified color from black and back again.

        :param channel: the channel which to send data to (R=0, G=1,
            B=2)
        :type channel: int
        :param index: the index of the LED
        :type index: int
        :param red: Red color intensity 0 is off, 255 is full red
            intensity
        :type red: int
        :param green: Green color intensity 0 is off, 255 is full green
            intensity
        :type green: int
        :param blue: Blue color intensity 0 is off, 255 is full blue
            intensity
        :type blue: int
        :param name: Use CSS color name as defined here: http://www.w3.org/TR/css3-color/
        :type name: str
        :param hex: Specify color using hexadecimal color value e.g.
            '#FF3366'
        :type hex: str
        :param repeats: Number of times to pulse the LED
        :type repeats: int
        :param duration: Duration for pulse in milliseconds
        :type duration: int
        :param steps: Number of gradient steps
        :type steps: int
        """
        self.turn_off()
        for x in range(repeats):
            self.morph(
                channel=channel,
                index=index,
                red=red,
                green=green,
                blue=blue,
                name=name,
                hex=hex,
                duration=duration,
                steps=steps,
            )
            self.morph(
                channel=channel,
                index=index,
                red=0,
                green=0,
                blue=0,
                duration=duration,
                steps=steps,
            )

    def blink(
        self,
        channel: int = 0,
        index: int = 0,
        red: int = 0,
        green: int = 0,
        blue: int = 0,
        name: str | None = None,
        hex: str | None = None,
        repeats: int = 1,
        delay: int = 500,
    ) -> None:
        """Blink the specified color.

        :param channel: the channel which to send data to (R=0, G=1,
            B=2)
        :type channel: int
        :param index: the index of the LED
        :type index: int
        :param red: Red color intensity 0 is off, 255 is full red
            intensity
        :type red: int
        :param green: Green color intensity 0 is off, 255 is full green
            intensity
        :type green: int
        :param blue: Blue color intensity 0 is off, 255 is full blue
            intensity
        :type blue: int
        :param name: Use CSS color name as defined here:
            U{http://www.w3.org/TR/css3-color/}
        :type name: str
        :param hex: Specify color using hexadecimal color value e.g.
            '#FF3366'
        :type hex: str
        :param repeats: Number of times to pulse the LED
        :type repeats: int
        :param delay: time in milliseconds to light LED for, and also
            between blinks
        :type delay: int
        """
        ms_delay = float(delay) / float(1000)
        for x in range(repeats):
            if x:
                time.sleep(ms_delay)
            self.set_color(
                channel=channel,
                index=index,
                red=red,
                green=green,
                blue=blue,
                name=name,
                hex=hex,
            )
            time.sleep(ms_delay)
            self.set_color(channel=channel, index=index)

    def morph(
        self,
        channel: int = 0,
        index: int = 0,
        red: int = 0,
        green: int = 0,
        blue: int = 0,
        name: str | None = None,
        hex: str | None = None,
        duration: int = 1000,
        steps: int = 50,
    ) -> None:
        """Morph to the specified color.

        :param channel: the channel which to send data to (R=0, G=1,
            B=2)
        :type channel: int
        :param index: the index of the LED
        :type index: int
        :param red: Red color intensity 0 is off, 255 is full red
            intensity
        :type red: int
        :param green: Green color intensity 0 is off, 255 is full green
            intensity
        :type green: int
        :param blue: Blue color intensity 0 is off, 255 is full blue
            intensity
        :type blue: int
        :param name: Use CSS color name as defined here:
            U{http://www.w3.org/TR/css3-color/}
        :type name: str
        :param hex: Specify color using hexadecimal color value e.g.
            '#FF3366'
        :type hex: str
        :param duration: Duration for morph in milliseconds
        :type duration: int
        :param steps: Number of gradient steps (default 50)
        :type steps: int
        """

        r_end, g_end, b_end = self._determine_rgb(
            red=red, green=green, blue=blue, name=name, hex=hex
        )
        # descale the above values
        r_end, g_end, b_end = remap_rgb_value_reverse(
            (r_end, g_end, b_end), self.max_rgb_value
        )

        r_start, g_start, b_start = remap_rgb_value_reverse(
            self._get_color_rgb(index), self.max_rgb_value
        )

        if r_start > 255 or g_start > 255 or b_start > 255:
            r_start = 0
            g_start = 0
            b_start = 0

        gradient = []

        steps += 1
        for n in range(1, steps):
            d = 1.0 * n / steps
            r = (r_start * (1 - d)) + (r_end * d)
            g = (g_start * (1 - d)) + (g_end * d)
            b = (b_start * (1 - d)) + (b_end * d)

            gradient.append((r, g, b))

        ms_delay = float(duration) / float(1000 * steps)

        self.set_color(
            channel=channel, index=index, red=r_start, green=g_start, blue=b_start
        )

        for grad in gradient:
            grad_r, grad_g, grad_b = map(int, grad)

            self.set_color(
                channel=channel, index=index, red=grad_r, green=grad_g, blue=grad_b
            )
            time.sleep(ms_delay)

        self.set_color(channel=channel, index=index, red=r_end, green=g_end, blue=b_end)

    def open_device(self, d):
        """Open backend.
        :param d: Device to open
        """
        if self.backend is None:
            raise BlinkStickException("Could not find BlinkStick...")

        if self.backend.is_kernel_driver_active(0):
            try:
                self.backend.detach_kernel_driver(0)
            except usb.core.USBError as e:
                raise BlinkStickException("Could not detach kernel driver: %s" % str(e))

        return True

    def get_inverse(self) -> bool:
        """Get the value of inverse mode. This applies only to BlinkStick. Please use :meth:`set_mode` for BlinkStick Pro
        to permanently set the inverse mode to the backend.

        :returns: True if inverse mode, otherwise false
        :rtype: bool
        """
        return self.inverse

    def set_inverse(self, value: bool) -> None:
        """Set inverse mode. This applies only to BlinkStick. Please use :meth:`set_mode` for BlinkStick Pro
        to permanently set the inverse mode to the backend.

        :param value: True/False to set the inverse mode
        :type value: bool
        """
        if type(value) is str:
            value = value.lower() == "true"  # type: ignore
        self.inverse = bool(value)

    def set_max_rgb_value(self, value: int) -> None:
        """Set RGB color limit. {set_color} function will automatically remap
        the values to maximum supplied.

        :param value: 0..255 maximum value for each R, G and B color
        :type value: int
        """
        # convert to int and clamp to 0..255
        value = max(0, min(255, int(value)))
        self.max_rgb_value = value

    def get_max_rgb_value(self) -> int:
        """Get RGB color limit. :meth:`set_color` function will automatically remap
        the values to maximum set.

        :returns: 0..255 maximum value for each R, G and B color
        :rtype: int
        """
        return self.max_rgb_value


class BlinkStickPro:
    """BlinkStickPro class is specifically designed to control the individually
    addressable LEDs connected to the backend. The tutorials section contains
    all the details on how to connect them to BlinkStick Pro.

    http://www.blinkstick.com/help/tutorials

    Code example on how you can use this class are available here:

    https://github.com/arvydas/blinkstick-python/wiki#code-examples-for-blinkstick-pro
    """

    r_led_count: int
    g_led_count: int
    b_led_count: int
    fps_count: int
    data_transmission_delay: float
    max_rgb_value: int
    data: list[list[list[int]]]
    bstick: BlinkStick | None

    def __init__(
        self,
        r_led_count: int = 0,
        g_led_count: int = 0,
        b_led_count: int = 0,
        delay: float = 0.002,
        max_rgb_value: int = 255,
    ):
        """Initialize BlinkStickPro class.

        :param r_led_count: number of LEDs on R channel
        :type r_led_count: int
        :param g_led_count: number of LEDs on G channel
        :type g_led_count: int
        :param b_led_count: number of LEDs on B channel
        :type b_led_count: int
        :param delay: default transmission delay between frames
        :type delay: int
        :param max_rgb_value: maximum color value for RGB channels
        :type max_rgb_value: int
        """

        self.r_led_count = r_led_count
        self.g_led_count = g_led_count
        self.b_led_count = b_led_count

        self.fps_count = -1

        self.data_transmission_delay = delay

        self.max_rgb_value = max_rgb_value

        # initialise data store for each channel
        # pre-populated with zeroes

        self.data = [[], [], []]

        for i in range(0, r_led_count):
            self.data[0].append([0, 0, 0])

        for i in range(0, g_led_count):
            self.data[1].append([0, 0, 0])

        for i in range(0, b_led_count):
            self.data[2].append([0, 0, 0])

        self.bstick = None

    def set_color(
        self,
        channel: int,
        index: int,
        r: int,
        g: int,
        b: int,
        remap_values: bool = True,
    ) -> None:
        """Set the color of a single pixel

        :param channel: R, G or B channel
        :type channel: int
        :param index: the index of LED on the channel
        :type index: int
        :param r: red color byte
        :type r: int
        :param g: green color byte
        :type g: int
        :param b: blue color byte
        :type b: int
        :param remap_values: remap the values to maximum set in
            :meth:`set_max_rgb_value`
        :type remap_values: bool
        """

        if remap_values:
            r, g, b = [remap_color(val, self.max_rgb_value) for val in [r, g, b]]

        self.data[channel][index] = [g, r, b]

    def get_color(self, channel: int, index: int) -> tuple[int, int, int]:
        """Get the current color of a single pixel.

        :param channel: the channel of the LED
        :type channel: int
        :param index: the index of the LED
        :type index: int

        :returns: 3-tuple for R, G and B values
        :rtype: (int, int, int)
        """

        val = self.data[channel][index]
        return val[1], val[0], val[2]

    def clear(self) -> None:
        """Set all pixels to black in the frame buffer."""
        for x in range(0, self.r_led_count):
            self.set_color(0, x, 0, 0, 0)

        for x in range(0, self.g_led_count):
            self.set_color(1, x, 0, 0, 0)

        for x in range(0, self.b_led_count):
            self.set_color(2, x, 0, 0, 0)

    def off(self) -> None:
        """Set all pixels to black on the device."""
        self.clear()
        self.send_data_all()

    def connect(self, serial: str | None = None):
        """Connect to the first BlinkStick found

        :param serial: Select the serial number of BlinkStick
        :type serial: str
        """

        if serial is None:
            self.bstick = find_first()
        else:
            self.bstick = find_by_serial(serial=serial)

        return self.bstick is not None

    def send_data(self, channel: int) -> None:
        """Send data stored in the internal buffer to the channel.

        :param channel: Channel to send data to
           - 0 - R pin on BlinkStick Pro board
           - 1 - G pin on BlinkStick Pro board
           - 2 - B pin on BlinkStick Pro board

        :type channel: int
        """
        if self.bstick is None:
            return

        packet_data = [item for sublist in self.data[channel] for item in sublist]

        try:
            self.bstick.set_led_data(channel, packet_data)
            time.sleep(self.data_transmission_delay)
        except Exception as e:
            print("Exception: {0}".format(e))

    def send_data_all(self) -> None:
        """Send data to all channels"""
        if self.r_led_count > 0:
            self.send_data(0)

        if self.g_led_count > 0:
            self.send_data(1)

        if self.b_led_count > 0:
            self.send_data(2)


class BlinkStickProMatrix(BlinkStickPro):
    """BlinkStickProMatrix class is specifically designed to control the individually
    addressable LEDs connected to the backend and arranged in a matrix. The tutorials section contains
    all the details on how to connect them to BlinkStick Pro with matrices.

    http://www.blinkstick.com/help/tutorials/blinkstick-pro-adafruit-neopixel-matrices

    Code example on how you can use this class are available here:

    https://github.com/arvydas/blinkstick-python/wiki#code-examples-for-blinkstick-pro

    Matrix is driven by using :meth:`BlinkStickProMatrix.set_color` with [x,y] coordinates and class automatically
    divides data into subsets and sends it to the matrices.

    For example, if you have 2 8x8 matrices connected to BlinkStickPro and you initialize
    the class with

    .. code-block:: python

        >>> matrix = BlinkStickProMatrix(r_columns=8, r_rows=8, g_columns=8, g_rows=8)

    Then you can set the internal framebuffer by using :meth:`set_color` command:

    .. code-block:: python

        >>> matrix.set_color(x=10, y=5, r=255, g=0, b=0)
        >>> matrix.set_color(x=6, y=3, r=0, g=255, b=0)

    And send data to both matrices in one go:

    .. code-block:: python

        >>> matrix.send_data_all()

    """

    r_columns: int
    r_rows: int
    g_columns: int
    g_rows: int
    b_columns: int
    b_rows: int
    rows: int
    cols: int
    matrix_data: list[list[int]]

    def __init__(
        self,
        r_columns: int = 0,
        r_rows: int = 0,
        g_columns: int = 0,
        g_rows: int = 0,
        b_columns: int = 0,
        b_rows: int = 0,
        delay: float = 0.002,
        max_rgb_value: int = 255,
    ):
        """Initialize BlinkStickProMatrix class.

        :param r_columns: number of matric columns for R channel
        :type r_columns: int
        :param g_columns: number of matric columns for R channel
        :type g_columns: int
        :param b_columns: number of matric columns for R channel
        :type b_columns: int
        :param delay: default transmission delay between frames
        :type delay: int
        :param max_rgb_value: maximum color value for RGB channels
        :type max_rgb_value: int
        """
        r_leds = r_columns * r_rows
        g_leds = g_columns * g_rows
        b_leds = b_columns * b_rows

        self.r_columns = r_columns
        self.r_rows = r_rows
        self.g_columns = g_columns
        self.g_rows = g_rows
        self.b_columns = b_columns
        self.b_rows = b_rows

        super(BlinkStickProMatrix, self).__init__(
            r_led_count=r_leds,
            g_led_count=g_leds,
            b_led_count=b_leds,
            delay=delay,
            max_rgb_value=max_rgb_value,
        )

        self.rows = max(r_rows, g_rows, b_rows)
        self.cols = r_columns + g_columns + b_columns

        # initialise data store for matrix pre-populated with zeroes
        self.matrix_data = []

        for i in range(0, self.rows * self.cols):
            self.matrix_data.append([0, 0, 0])

    def set_color(
        self, x: int, y: int, r: int, g: int, b: int, remap_values: bool = True
    ) -> None:
        """Set the color of a single pixel in the internal framebuffer.

        :param x: the x location in the matrix
        :type x: int
        :param y: the y location in the matrix
        :type y: int
        :param r: red color byte
        :type r: int
        :param g: green color byte
        :type g: int
        :param b: blue color byte
        :type b: int
        :param remap_values: Automatically remap values based on the
            {max_rgb_value} supplied in the constructor
        :type remap_values: bool
        """

        if remap_values:
            r, g, b = [remap_color(val, self.max_rgb_value) for val in [r, g, b]]

        self.matrix_data[self._coord_to_index(x, y)] = [g, r, b]

    def _coord_to_index(self, x: int, y: int) -> int:
        return y * self.cols + x

    def get_color(self, x: int, y: int) -> tuple[int, int, int]:
        """Get the current color of a single pixel.

        :param x: x coordinate of the internal framebuffer
        :type x: int
        :param y: y coordinate of the internal framebuffer
        :type y: int

        :returns: 3-tuple for R, G and B values
        :rtype: (int, int, int)
        """

        val = self.matrix_data[self._coord_to_index(x, y)]
        return val[1], val[0], val[2]

    def shift_left(self, remove: bool = False) -> None:
        """Shift all LED values in the matrix to the left

        :param remove: whether to remove the pixels on the last column
            or move the to the first column
        :type remove: bool
        """
        if not remove:
            temp = []
            for y in range(0, self.rows):
                temp.append(self.get_color(0, y))

        for y in range(0, self.rows):
            for x in range(0, self.cols - 1):
                r, g, b = self.get_color(x + 1, y)

                self.set_color(x, y, r, g, b, False)

        if remove:
            for y in range(0, self.rows):
                self.set_color(self.cols - 1, y, 0, 0, 0, False)
        else:
            for y in range(0, self.rows):
                col = temp[y]
                self.set_color(self.cols - 1, y, col[0], col[1], col[2], False)

    def shift_right(self, remove: bool = False) -> None:
        """Shift all LED values in the matrix to the right

        :param remove: whether to remove the pixels on the last column
            or move the to the first column
        :type remove: bool
        """

        if not remove:
            temp = []
            for y in range(0, self.rows):
                temp.append(self.get_color(self.cols - 1, y))

        for y in range(0, self.rows):
            for x in reversed(range(1, self.cols)):
                r, g, b = self.get_color(x - 1, y)

                self.set_color(x, y, r, g, b, False)

        if remove:
            for y in range(0, self.rows):
                self.set_color(0, y, 0, 0, 0, False)
        else:
            for y in range(0, self.rows):
                col = temp[y]
                self.set_color(0, y, col[0], col[1], col[2], False)

    def shift_down(self, remove: bool = False) -> None:
        """Shift all LED values in the matrix down

        :param remove: whether to remove the pixels on the last column
            or move the to the first column
        :type remove: bool
        """

        if not remove:
            temp = []
            for x in range(0, self.cols):
                temp.append(self.get_color(x, self.rows - 1))

        for y in reversed(range(1, self.rows)):
            for x in range(0, self.cols):
                r, g, b = self.get_color(x, y - 1)

                self.set_color(x, y, r, g, b, False)

        if remove:
            for x in range(0, self.cols):
                self.set_color(x, 0, 0, 0, 0, False)
        else:
            for x in range(0, self.cols):
                col = temp[x]
                self.set_color(x, 0, col[0], col[1], col[2], False)

    def shift_up(self, remove: bool = False):
        """Shift all LED values in the matrix up

        :param remove: whether to remove the pixels on the last column
            or move the to the first column
        :type remove: bool
        """

        if not remove:
            temp = []
            for x in range(0, self.cols):
                temp.append(self.get_color(x, 0))

        for x in range(0, self.cols):
            for y in range(0, self.rows - 1):
                r, g, b = self.get_color(x, y + 1)

                self.set_color(x, y, r, g, b, False)

        if remove:
            for x in range(0, self.cols):
                self.set_color(x, self.rows - 1, 0, 0, 0, False)
        else:
            for x in range(0, self.cols):
                col = temp[x]
                self.set_color(x, self.rows - 1, col[0], col[1], col[2], False)

    def number(self, x: int, y: int, n: int, r: int, g: int, b: int) -> None:
        """Render a 3x5 number n at location x,y and r,g,b color

        :param x: the x location in the matrix (left of the number)
        :type x: int
        :param y: the y location in the matrix (top of the number)
        :type y: int
        :param n: number digit to render 0..9
        :type n: int
        :param r: red color byte
        :type r: int
        :param g: green color byte
        :type g: int
        :param b: blue color byte
        :type b: int
        """
        if n == 0:
            self.rectangle(x, y, x + 2, y + 4, r, g, b)
        elif n == 1:
            self.line(x + 1, y, x + 1, y + 4, r, g, b)
            self.line(x, y + 4, x + 2, y + 4, r, g, b)
            self.set_color(x, y + 1, r, g, b)
        elif n == 2:
            self.line(x, y, x + 2, y, r, g, b)
            self.line(x, y + 2, x + 2, y + 2, r, g, b)
            self.line(x, y + 4, x + 2, y + 4, r, g, b)
            self.set_color(x + 2, y + 1, r, g, b)
            self.set_color(x, y + 3, r, g, b)
        elif n == 3:
            self.line(x, y, x + 2, y, r, g, b)
            self.line(x, y + 2, x + 2, y + 2, r, g, b)
            self.line(x, y + 4, x + 2, y + 4, r, g, b)
            self.set_color(x + 2, y + 1, r, g, b)
            self.set_color(x + 2, y + 3, r, g, b)
        elif n == 4:
            self.line(x, y, x, y + 2, r, g, b)
            self.line(x + 2, y, x + 2, y + 4, r, g, b)
            self.set_color(x + 1, y + 2, r, g, b)
        elif n == 5:
            self.line(x, y, x + 2, y, r, g, b)
            self.line(x, y + 2, x + 2, y + 2, r, g, b)
            self.line(x, y + 4, x + 2, y + 4, r, g, b)
            self.set_color(x, y + 1, r, g, b)
            self.set_color(x + 2, y + 3, r, g, b)
        elif n == 6:
            self.line(x, y, x + 2, y, r, g, b)
            self.line(x, y + 2, x + 2, y + 2, r, g, b)
            self.line(x, y + 4, x + 2, y + 4, r, g, b)
            self.set_color(x, y + 1, r, g, b)
            self.set_color(x + 2, y + 3, r, g, b)
            self.set_color(x, y + 3, r, g, b)
        elif n == 7:
            self.line(x + 1, y + 2, x + 1, y + 4, r, g, b)
            self.line(x, y, x + 2, y, r, g, b)
            self.set_color(x + 2, y + 1, r, g, b)
        elif n == 8:
            self.line(x, y, x + 2, y, r, g, b)
            self.line(x, y + 2, x + 2, y + 2, r, g, b)
            self.line(x, y + 4, x + 2, y + 4, r, g, b)
            self.set_color(x, y + 1, r, g, b)
            self.set_color(x + 2, y + 1, r, g, b)
            self.set_color(x + 2, y + 3, r, g, b)
            self.set_color(x, y + 3, r, g, b)
        elif n == 9:
            self.line(x, y, x + 2, y, r, g, b)
            self.line(x, y + 2, x + 2, y + 2, r, g, b)
            self.line(x, y + 4, x + 2, y + 4, r, g, b)
            self.set_color(x, y + 1, r, g, b)
            self.set_color(x + 2, y + 1, r, g, b)
            self.set_color(x + 2, y + 3, r, g, b)

    def rectangle(
        self, x1: int, y1: int, x2: int, y2: int, r: int, g: int, b: int
    ) -> None:
        """Draw a rectangle with its corners at x1:y1 and x2:y2

        :param x1: the x1 location in the matrix for first corner of the
            rectangle
        :type x1: int
        :param y1: the y1 location in the matrix for first corner of the
            rectangle
        :type y1: int
        :param x2: the x2 location in the matrix for second corner of
            the rectangle
        :type x2: int
        :param y2: the y2 location in the matrix for second corner of
            the rectangle
        :type y2: int
        :param r: red color byte
        :type r: int
        :param g: green color byte
        :type g: int
        :param b: blue color byte
        :type b: int
        """

        self.line(x1, y1, x1, y2, r, g, b)
        self.line(x1, y1, x2, y1, r, g, b)
        self.line(x2, y1, x2, y2, r, g, b)
        self.line(x1, y2, x2, y2, r, g, b)

    def line(
        self, x1: int, y1: int, x2: int, y2: int, r: int, g: int, b: int
    ) -> list[tuple[int, int]]:
        """Draw a line from x1:y1 and x2:y2

        :param x1: the x1 location in the matrix for the start of the
            line
        :type x1: int
        :param y1: the y1 location in the matrix for the start of the
            line
        :type y1: int
        :param x2: the x2 location in the matrix for the end of the line
        :type x2: int
        :param y2: the y2 location in the matrix for the end of the line
        :type y2: int
        :param r: red color byte
        :type r: int
        :param g: green color byte
        :type g: int
        :param b: blue color byte
        :type b: int
        :returns: list of points that were drawn
        :rtype: list[tuple[int, int]]
        """
        points = []
        is_steep = abs(y2 - y1) > abs(x2 - x1)
        if is_steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
        rev = False
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            rev = True
        delta_x = x2 - x1
        delta_y = abs(y2 - y1)
        error = int(delta_x / 2)
        y = y1
        y_step = None

        if y1 < y2:
            y_step = 1
        else:
            y_step = -1
        for x in range(x1, x2 + 1):
            if is_steep:
                # print y, "~", x
                self.set_color(y, x, r, g, b)
                points.append((y, x))
            else:
                # print x, " ", y
                self.set_color(x, y, r, g, b)
                points.append((x, y))
            error -= delta_y
            if error < 0:
                y += y_step
                error += delta_x
                # Reverse the list if the coordinates were reversed
        if rev:
            points.reverse()
        return points

    def clear(self) -> None:
        """Set all pixels to black in the cached matrix"""
        for y in range(0, self.rows):
            for x in range(0, self.cols):
                self.set_color(x, y, 0, 0, 0)

    def send_data(self, channel: int) -> None:
        """Send data stored in the internal buffer to the channel.

        :param channel: Channel to send data to
           - 0 - R pin on BlinkStick Pro board
           - 1 - G pin on BlinkStick Pro board
           - 2 - B pin on BlinkStick Pro board

        :type channel: int
        """

        start_col = 0
        end_col = 0

        if channel == 0:
            start_col = 0
            end_col = self.r_columns

        if channel == 1:
            start_col = self.r_columns
            end_col = start_col + self.g_columns

        if channel == 2:
            start_col = self.r_columns + self.g_columns
            end_col = start_col + self.b_columns

        self.data[channel] = []

        # slice the huge array to individual packets
        for y in range(0, self.rows):
            start = y * self.cols + start_col
            end = y * self.cols + end_col

            self.data[channel].extend(self.matrix_data[start:end])

        super(BlinkStickProMatrix, self).send_data(channel)


def _find_blicksticks(find_all: bool = True) -> list[BlinkStick] | None:
    if sys.platform == "win32":
        devices = hid.HidDeviceFilter(
            vendor_id=VENDOR_ID, product_id=PRODUCT_ID
        ).get_devices()
        if find_all:
            return devices
        elif len(devices) > 0:
            return devices[0]
        else:
            return None

    else:
        return usb.core.find(
            find_all=find_all, idVendor=VENDOR_ID, idProduct=PRODUCT_ID
        )


def find_all() -> list[BlinkStick]:
    """Find all attached BlinkStick devices.

    :returns: a list of BlinkStick objects or None if no devices found
    :rtype: BlinkStick[] | None
    """
    result: list[BlinkStick] = []
    if (found_devices := USBBackend.find_blinksticks()) is None:
        return result
    for d in found_devices:
        result.extend([BlinkStick(device=d)])

    return result


def find_first() -> BlinkStick | None:
    """Find first attached BlinkStick.

    :returns: BlinkStick object or None if no devices are found
    :rtype: BlinkStick | None
    """
    d = USBBackend.find_blinksticks(find_all=False)

    if d:
        return BlinkStick(device=d)

    return None


def find_by_serial(serial: str = "") -> BlinkStick | None:
    """Find BlinkStick backend based on serial number.

    :returns: BlinkStick object or None if no devices are found
    :rtype: BlinkStick | None
    """

    devices = USBBackend.find_by_serial(serial=serial)

    if devices:
        return BlinkStick(device=devices[0])

    return None


def get_blinkstick_package_version() -> str:
    return version("blinkstick")
