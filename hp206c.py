import time

import smbus


class HP206C(object):
    """Driver for getting temperature and pressure data from HP206C."""
    address = 0x76
    soft_reset = 0x06
    conversion_time = {
        128: 2.1,
        256: 4.1,
        512: 8.2,
        1024: 16.4,
        2048: 32.8,
        4096: 65.6
    }

    def __init__(self, port=1, metric=True):
        self.bus = smbus.SMBus(port)
        self.metric = metric

    def do_reset(self):
        self.bus.write_byte(self.address, self.soft_reset)
