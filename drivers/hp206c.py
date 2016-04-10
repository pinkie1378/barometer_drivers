from functools import partial
import time

from .basei2c import BaseI2CDriver


class HP206C(BaseI2CDriver):
    """Driver for getting temperature and pressure data from HP206C."""

    commands = {
        'soft_reset'        : 0x06,
        'adc_pressure_temp' : partial(BaseI2CDriver.do_bitwise_or, 0x40, 0x00),
        'adc_temp'          : partial(BaseI2CDriver.do_bitwise_or, 0x40, 0x02),
        'read_pressure_temp': 0x10,
        'read_altitude_temp': 0x11,
        'read_pressure'     : 0x30,
        'read_altitude'     : 0x31,
        'read_temp'         : 0x32,
        'analog_calibrate'  : 0x28,
        'read_register'     : partial(BaseI2CDriver.do_bitwise_or, 0x80),
        'write_register'    : partial(BaseI2CDriver.do_bitwise_or, 0xc0)
    }
    registers = {
        'altitude_offset'        : (0x00, 0x01),
        'high_pressure_threshold': (0x02, 0x03),
        'mid_pressure_threshold' : (0x04, 0x05),
        'low_pressure_threshold' : (0x06, 0x07),
        'high_temp_threshold'    : 0x08,
        'mid_temp_threshold'     : 0x09,
        'low_temp_threshold'     : 0x0a,
        'interrupt_enable'       : 0x0b,
        'interrupt_configure'    : 0x0c,
        'interrupt_status'       : 0x0d,
        'interrupt_events'       : 0x0e,
        'compensation'           : 0x0f
    }
    osr_conversion = {
        128 : {'command': 0x14, 'msec': 2.1},
        256 : {'command': 0x10, 'msec': 4.1},
        512 : {'command': 0x0c, 'msec': 8.2},
        1024: {'command': 0x08, 'msec': 16.4},
        2048: {'command': 0x04, 'msec': 32.8},
        4096: {'command': 0x00, 'msec': 65.6}
    }

    def __init__(self, port=1, oversampling_rate=4096, metric=True):
        super(BaseI2CDriver, self).__init__(port, address=0x76)
        self.oversampling_rate = oversampling_rate
        self.metric = metric

    @property
    def oversampling_rate(self):
        return self.__osr

    @oversampling_rate.setter
    def oversampling_rate(self, osr):
        assert osr in self.osr_conversion.keys(), """\
            '{}' is not a valid OSR value. Choose 128, 256, 512, 1024, \
            2048, or 4096.""".format(osr)
        self.__osr = osr

    def send_reset(self):
        """Send soft reset command. Once received and executed, all memory will
        be reset to default values, followed by a complete power-up sequence.
        """
        self.write_byte(self.commands['soft_reset'])

    def send_adc_command(self, temperature_only=False):
        """Send analog-to-digital converter command, which tells HP206C
        to make a new reading.

        :param bool temperature_only: When True, only measure temperature.
         When False, measure both temperature and pressure/altitude.
        """
        osr = self.osr_conversion[self.oversampling_rate]['command']
        if temperature_only:
            self.write_byte(self.commands['adc_temp'](osr))
        else:
            self.write_byte(self.commands['adc_pressure_temp'](osr))

    def is_ready():
        """Check DEV_RDY bit (6) on the interrupt status (INT_SRC) register."""
        register = self.registers['interrupt_status']
        command = self.commands['read_register'](register)
        status = self.read_byte_data(command)
        return BaseI2CDriver.is_bit_set(status, 6)
