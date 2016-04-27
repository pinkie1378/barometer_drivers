from abc import ABCMeta, abstractmethod

from .basei2c import BaseI2CDriver


class BaseBarometer(BaseI2CDriver):
    """Interface for barometer drivers."""
    __metaclass__ = ABCMeta

    osr_conversion = {}

    def __init__(self, address, oversampling_rate, port):
        super(BaseBarometer, self).__init__(address, port)
        self.oversampling_rate = oversampling_rate

    @property
    def oversampling_rate(self):
        return self.__osr

    @oversampling_rate.setter
    def oversampling_rate(self, osr):
        valid_osrs = sorted(list(self.osr_conversion.keys()))
        message = "'{}' is not a valid OSR value. Choose {}"
        assert osr in valid_osrs, \
            message.format(osr, ', '.join(map(str, valid_osrs)))
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
