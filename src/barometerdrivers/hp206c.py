from functools import partial
import time

from .absi2cbarometer import AbsI2CBarometer, OSRValue
from .util import array_block_to_signed_int, do_bitwise_or, is_bit_set


class _HP206Ccommands(object):
    """Command bits for HP206C barometer."""
    soft_reset = 0x06
    adc_pressure_temp = partial(do_bitwise_or, 0x40, 0x00)
    adc_temp = partial(do_bitwise_or, 0x40, 0x02)
    read_temp_pressure = 0x10
    read_temp_altitude = 0x11
    read_pressure = 0x30
    read_altitude = 0x31
    read_temp = 0x32
    analog_calibrate = 0x28
    read_register = partial(do_bitwise_or, 0x80)
    write_register = partial(do_bitwise_or, 0xc0)


class _HP206Cregisters(object):
    """Register bits for HP206C barometer."""
    altitude_offset = (0x00, 0x01)
    high_pressure_threshold = (0x02, 0x03)
    mid_pressure_threshold = (0x04, 0x05)
    low_pressure_threshold = (0x06, 0x07)
    high_temp_threshold = 0x08
    mid_temp_threshold = 0x09
    low_temp_threshold = 0x0a
    interrupt_enable = 0x0b
    interrupt_configure = 0x0c
    interrupt_status = 0x0d
    interrupt_events = 0x0e
    compensation = 0x0f


class HP206C(AbsI2CBarometer):
    """Driver for getting temperature and pressure data from HP206C."""

    commands = _HP206Ccommands()
    registers = _HP206Cregisters()
    osr_conversion = {
        128 : OSRValue(0x14, 2.1),
        256 : OSRValue(0x10, 4.1),
        512 : OSRValue(0x0c, 8.2),
        1024: OSRValue(0x08, 16.4),
        2048: OSRValue(0x04, 32.8),
        4096: OSRValue(0x00, 65.6)
    }

    def __init__(self, oversampling_rate=4096, port=1):
        super(HP206C, self).__init__(0x76, oversampling_rate, port)
        self.send_reset()
        self.wait_until_ready(delay=0.1)

    def send_reset(self):
        """Send soft reset command. Once received and executed, all memory will
        be reset to default values, followed by a complete power-up sequence.
        """
        self.i2c.write_byte(self.commands.soft_reset)

    def send_adc_command(self, temperature_only=False):
        """Send analog-to-digital converter command, which tells HP206C
        to make a new reading.

        :param bool temperature_only: When True, only measure temperature.
         When False, measure both temperature and pressure/altitude.
        """
        osr = self.osr_conversion[self.oversampling_rate].command
        if temperature_only:
            self.i2c.write_byte(self.commands.adc_temp(osr))
        else:
            self.i2c.write_byte(self.commands.adc_pressure_temp(osr))

    def is_ready(self):
        """Check DEV_RDY bit (6) on the interrupt status (INT_SRC) register.

        :return bool: Device is available for data access.
        """
        register = self.registers.interrupt_status
        command = self.commands.read_register(register)
        status = self.i2c.read_byte_data(command)
        return is_bit_set(status, 6)

    def wait_until_ready(self, delay=0.0, poll_rate=0.01):
        """
        :param float delay: Initial blocking period in sec.
        :param float poll_rate: Subsequent device polling rate in sec.
        """
        time.sleep(delay)
        while not self.is_ready():
            time.sleep(poll_rate)

    def read_temperature(self):
        """
        :return float: Temperature in degrees C.
        """
        delay = self.osr_conversion[self.oversampling_rate].msec / 1000
        self.send_adc_command(temperature_only=True)
        self.wait_until_ready(delay=delay)
        command = self.commands.read_temp
        array = self.i2c.read_block_data(command, 3)
        return array_block_to_signed_int(array) / 100.0

    def read_pressure(self):
        """
        :return float: Pressure in mBar
        """
        delay = self.osr_conversion[self.oversampling_rate].msec / 500
        self.send_adc_command()
        self.wait_until_ready(delay=delay)
        command = self.commands.read_pressure
        array = self.i2c.read_block_data(command, 3)
        return array_block_to_signed_int(array) / 100.0

    def read_temperature_and_pressure(self):
        """
        :return tuple: Temperature in degrees C, pressure in mBar.
        """
        delay = self.osr_conversion[self.oversampling_rate].msec / 500
        self.send_adc_command()
        self.wait_until_ready(delay=delay)
        command = self.commands.read_temp_pressure
        array = self.i2c.read_block_data(command, 6)
        temperature = array_block_to_signed_int(array[:3]) / 100.0
        pressure = array_block_to_signed_int(array[3:]) / 100.0
        return temperature, pressure
