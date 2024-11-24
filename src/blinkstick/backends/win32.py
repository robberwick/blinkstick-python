"""
This module provides a backend for the BlinkStick using the pywinusb library.
"""

from __future__ import annotations

import sys
from ctypes import *

from pywinusb import hid  # type: ignore

from blinkstick.constants import VENDOR_ID, PRODUCT_ID
from blinkstick.backends.base import BaseBackend
from blinkstick.exceptions import BlinkStickException


class Win32Backend(BaseBackend[hid.HidDevice]):
    """
    This class provides the USB backend for BlinkStick devices on Windows systems, using the `pywinusb` library.
    """

    serial: str
    device: hid.HidDevice
    reports: list[hid.core.HidReport]

    def __init__(self, device=None):
        super().__init__()
        self.device = device
        if device:
            self.device.open()
            self.reports = self.device.find_feature_reports()
            self.serial = self.get_serial()

    @staticmethod
    def find_by_serial(serial: str) -> list[hid.HidDevice] | None:
        """
        Find a BlinkStick device by serial number.

        :param serial:
        :return: A list of `hid.HidDevice` objects, or None if no devices are found.
        """
        found_devices = Win32Backend.find_blinksticks() or []
        devices = [d for d in found_devices if d.serial_number == serial]

        if len(devices) > 0:
            return devices

        return None

    def _refresh_device(self) -> bool:
        """
        Refresh the device instance.
        :rtype: bool
        """
        # TODO This is weird semantics. fix up return values to be more sensible
        if not self.serial:
            return False
        if devices := self.find_by_serial(self.serial):
            self.device = devices[0]
            self.device.open()
            self.reports = self.device.find_feature_reports()
            return True

    @staticmethod
    def find_blinksticks(find_all: bool = True) -> list[hid.HidDevice] | None:
        """
        Find all BlinkStick devices.

        :param find_all: Find all devices or just the first one.
        :return: A list of `hid.HidDevice` objects, or None if no devices are found.
        """
        devices = hid.HidDeviceFilter(
            vendor_id=VENDOR_ID, product_id=PRODUCT_ID
        ).get_devices()
        if find_all:
            return devices
        elif len(devices) > 0:
            return devices[0]
        else:
            return None

    def control_transfer(
        self, bmRequestType, bRequest, wValue, wIndex, data_or_wLength
    ):
        """
        Perform a control transfer on the device.

        :param bmRequestType:
        :param bRequest:
        :param wValue:
        :param wIndex:
        :param data_or_wLength:
        :return: None
        """
        if bmRequestType == 0x20:
            if sys.version_info[0] < 3:
                data = (c_ubyte * len(data_or_wLength))(
                    *[c_ubyte(ord(c)) for c in data_or_wLength]
                )
            else:
                data = (c_ubyte * len(data_or_wLength))(
                    *[c_ubyte(c) for c in data_or_wLength]
                )
            data[0] = wValue
            if not self.device.send_feature_report(data):
                if self._refresh_device():
                    self.device.send_feature_report(data)
                else:
                    raise BlinkStickException(
                        "Could not communicate with BlinkStick {0} - it may have been removed".format(
                            self.serial
                        )
                    )

        elif bmRequestType == 0x80 | 0x20:
            return self.reports[wValue - 1].get()

    def get_serial(self) -> str:
        """
        Get the serial number of the device.

        :return: The serial number of the device.
        """
        return str(self.device.serial_number)

    def get_manufacturer(self) -> str:
        """
        Get the manufacturer of the device.

        :return: The manufacturer of the device.
        """
        return str(self.device.vendor_name)

    def get_version_attribute(self) -> int:
        """
        Get the version attribute of the device.

        :return: The version attribute of the device.
        """
        return int(self.device.version_number)

    def get_description(self) -> str:
        """
        Get the description of the device.

        :return: The description of the device.
        """
        return str(self.device.product_name)
