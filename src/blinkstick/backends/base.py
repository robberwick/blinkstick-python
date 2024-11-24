"""
This module provides the base USB backend class for BlinkStick devices.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from typing import TypeVar, Generic

T = TypeVar("T")


class BaseBackend(ABC, Generic[T]):
    """
    This class provides the Abstract Base Class USB backend for BlinkStick devices.

    .. Note:: This class should not be instantiated directly. Use one of the subclasses instead.

    :param T: The type of the device.
    :type T: TypeVar

    """

    serial: str | None

    def __init__(self):
        self.serial = None

    @abstractmethod
    def _refresh_device(self):
        """
        Refresh the device instance.

        :raises NotImplementedError: This method should not be used directly.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def find_blinksticks(find_all: bool = True) -> list[T] | None:
        """
        Find all BlinkStick devices.

        :type find_all: bool
        :param find_all:
        :raises NotImplementedError: This method should not be used directly.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def find_by_serial(serial: str) -> list[T] | None:
        """
        Find a BlinkStick device by serial number.

        :type serial: str
        :param serial:
        :return: list[T] | None
        :raises NotImplementedError: This method should not be used directly.
        """
        raise NotImplementedError

    @abstractmethod
    def control_transfer(
        self,
        bmRequestType: int,
        bRequest: int,
        wValue: int,
        wIndex: int,
        data_or_wLength: bytes | int,
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
        raise NotImplementedError

    @abstractmethod
    def get_serial(self) -> str:
        """
        Get the serial number of the device.

        :returns: The serial number of the device.
        :raises NotImplementedError: This method should not be used directly.
        """
        raise NotImplementedError

    @abstractmethod
    def get_manufacturer(self) -> str:
        """
        Get the manufacturer of the device.

        :returns: The manufacturer of the device.
        :raises NotImplementedError: This method should not be used directly.
        """
        raise NotImplementedError

    @abstractmethod
    def get_version_attribute(self) -> int:
        """
        Get the version attribute of the device.

        :return: The version attribute of the device.
        :raises NotImplementedError: This method should not be used directly.
        """
        raise NotImplementedError

    @abstractmethod
    def get_description(self) -> str:
        """
        Get the description of the device.

        :return: The description of the device.
        :raises NotImplementedError: This method should not be used directly.
        """
        raise NotImplementedError
