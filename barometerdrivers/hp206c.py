from functools import partial
import time

from .abstractbarometer import BaseBarometer


class HP206C(BaseBarometer):
    """Driver for getting temperature and pressure data from HP206C."""

    commands = {
        'soft_reset'        : 0x06,
        'adc_pressure_temp' : partial(BaseBarometer.do_bitwise_or, 0x40, 0x00),
        'adc_temp'          : partial(BaseBarometer.do_bitwise_or, 0x40, 0x02),
        'read_temp_pressure': 0x10,
        'read_temp_altitude': 0x11,
        'read_pressure'     : 0x30,
        'read_altitude'     : 0x31,
        'read_temp'         : 0x32,
        'analog_calibrate'  : 0x28,
        'read_register'     : partial(BaseBarometer.do_bitwise_or, 0x80),
        'write_register'    : partial(BaseBarometer.do_bitwise_or, 0xc0)
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

    def __init__(self, oversampling_rate=4096, port=1):
        super(HP206C, self).__init__(0x76, oversampling_rate, port)

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

    def is_ready(self):
        """Check DEV_RDY bit (6) on the interrupt status (INT_SRC) register.

        :return bool: Device is available for data access.
        """
        register = self.registers['interrupt_status']
        command = self.commands['read_register'](register)
        status = self.read_byte_data(command)
        return self.is_bit_set(status, 6)

    def wait_until_ready(self, delay=0.0, poll_rate=0.01):
        """
        :param float delay: Initial blocking period in sec.
        :param float poll_rate: Subsequent device polling rate in sec.
        """
        time.sleep(delay)
        while not self.is_ready():
            print('Not ready yet')
            time.sleep(poll_rate)

    def read_temperature(self):
        """
        :return float: Temperature in degrees C.
        """
        delay = self.osr_conversion[self.oversampling_rate]['msec'] / 1000
        self.send_adc_command(temperature_only=True)
        self.wait_until_ready(delay=delay)
        command = self.commands['read_temp']
        array = self.read_block_data(command, 3)
        return self.array_block_to_int(array) / 100.0

    def read_pressure(self):
        """
        :return float: Pressure in mBar
        """
        delay = self.osr_conversion[self.oversampling_rate]['msec'] / 500
        self.send_adc_command()
        self.wait_until_ready(delay=delay)
        command = self.commands['read_pressure']
        array = self.read_block_data(command, 3)
        return self.array_block_to_int(array) / 100.0

    def read_temperature_and_pressure(self):
        """
        :return tuple: Temperature in degrees C, pressure in mBar.
        """
        delay = self.osr_conversion[self.oversampling_rate]['msec'] / 500
        self.send_adc_command()
        self.wait_until_ready(delay=delay)
        command = self.commands['read_temp_pressure']
        array = self.read_block_data(command, 6)
        temperature = self.array_block_to_int(array[:3]) / 100.0
        pressure = self.array_block_to_int(array[3:]) / 100.0
        return temperature, pressure
