import time

from .abci2c import BaseI2CDriver


class HP206C(BaseI2CDriver):
    """Driver for getting temperature and pressure data from HP206C."""
    soft_reset = 0x06
    conversion_time = {
        128: 2.1,
        256: 4.1,
        512: 8.2,
        1024: 16.4,
        2048: 32.8,
        4096: 65.6
    }

    def __init__(self, port=1, oversampling_rate=4096, metric=True):
        super(BaseI2CDriver, self).__init__(port, address=0x76)
        self.oversampling_rate = oversampling_rate
        self.metric = metric

    @property
    def oversampling_rate(self):
        return self.__oversampling_rate

    @oversampling_rate.setter
    def oversampling_rate(self, osr):
        assert osr in self.conversion_time.keys(), """\
            '{}' is not a valid OSR value. Choose 128, 256, 512, 1024, \
            2048, or 4096.""".format(osr)
        self.__oversampling_rate = osr

    def do_reset(self):
        self.bus.write_byte(self.address, self.soft_reset)
