from __future__ import annotations

import usb.core
import usb.util

from blinkstick.constants import VENDOR_ID, PRODUCT_ID
from blinkstick.backends.base import BaseBackend
from blinkstick.exceptions import BlinkStickException


class UnixLikeBackend(BaseBackend):

    def __init__(self, device=None):
        self.device = device
        super().__init__()
        if device:
            self.open_device()
            self.serial = self.get_serial()

    def open_device(self):
        if self.device is None:
            raise BlinkStickException("Could not find BlinkStick...")

        if self.device.is_kernel_driver_active(0):
            try:
                self.device.detach_kernel_driver(0)
            except usb.core.USBError as e:
                raise BlinkStickException("Could not detach kernel driver: %s" % str(e))

        return True

    def _refresh_device(self):
        if not self.serial:
            return False
        if devices := self.find_by_serial(self.serial):
            self.device = devices[0]
            self.open_device()
            return True

    @staticmethod
    def find_blinksticks(find_all: bool = True):
        return usb.core.find(find_all=find_all, idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    @staticmethod
    def find_by_serial(serial: str) -> list | None:
        for d in UnixLikeBackend.find_blinksticks():
            try:
                if usb.util.get_string(d, 3, 1033) == serial:
                    devices = [d]
                    return devices
            except Exception as e:
                print("{0}".format(e))

    def control_transfer(self, bmRequestType: int, bRequest: int, wValue: int, wIndex: int,
                         data_or_wLength: bytes | int):
        try:
            return self.device.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data_or_wLength)
        except usb.USBError:
            # Could not communicate with BlinkStick backend
            # attempt to find it again based on serial

            if self._refresh_device():
                return self.device.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data_or_wLength)
            else:
                raise BlinkStickException("Could not communicate with BlinkStick {0} - it may have been removed".format(self.serial))

    def get_serial(self) -> str:
        return self._usb_get_string(3)

    def get_manufacturer(self):
        return self._usb_get_string(1)

    def get_version_attribute(self):
        return self.device.bcdDevice

    def get_description(self):
        return self._usb_get_string(2)

    def _usb_get_string(self, index):
        try:
            return usb.util.get_string(self.device, index, 1033)
        except usb.USBError:
            # Could not communicate with BlinkStick backend
            # attempt to find it again based on serial

            if self._refresh_device():
                return usb.util.get_string(self.device, index, 1033)
            else:
                raise BlinkStickException("Could not communicate with BlinkStick {0} - it may have been removed".format(self.serial))