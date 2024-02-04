from abc import ABCMeta, abstractmethod
from collections import namedtuple

from .i2creadwrite import I2CReadWrite

OSRValue = namedtuple("OSRvalue", ["command", "msec"])


class AbsI2CBarometer(object):
    """Base class for I2C barometer drivers."""

    __metaclass__ = ABCMeta

    osr_conversion = {}

    def __init__(self, address, oversampling_rate, port):
        self.i2c = I2CReadWrite(address, port)
        self.oversampling_rate = oversampling_rate

    @property
    def oversampling_rate(self):
        return self.__osr

    @oversampling_rate.setter
    def oversampling_rate(self, osr):
        valid_osrs = sorted(self.osr_conversion.keys())
        msg = "'{}' is not a valid OSR value. Choose {}."
        if osr not in valid_osrs:
            raise ValueError(msg.format(osr, ", ".join(map(str, valid_osrs))))
        self.__osr = osr

    @abstractmethod
    def send_reset(self):
        pass  # pragma: no cover

    @abstractmethod
    def read_temperature(self):
        pass  # pragma: no cover

    @abstractmethod
    def read_pressure(self):
        pass  # pragma: no cover

    @abstractmethod
    def read_temperature_and_pressure(self):
        pass  # pragma: no cover
