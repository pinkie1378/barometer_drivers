from abc import ABCMeta, abstractmethod
from enum import Enum
from functools import partial
import time

from .basebarometer import BaseBarometer


class Reading(Enum):
    TEMPERATURE = 't'
    PRESSURE = 'p'


def _adc_cmd(pressure_cmd, reading_type):
    """There are 2 ADCs, one for temperature and one for pressure. The
    temperature commands have 1 extra bit.

    :param int pressure_cmd: Pressure ADC command bit.
    :param Reading reading_type: Temperature or pressure.
    :return int: Correct command bit for reading temperature or pressure.
    """
    if reading_type == Reading.PRESSURE:
        return pressure_cmd
    else:
        return pressure_cmd | 0x10


class BaseMS5803(BaseBarometer):
    """Base class driver for reading temperature and pressure data from the
    MS5803 family of barometers.
    """
    reset = 0x1e
    read_adc = 0x00
    prom_coefficients = {
        'sens_t1' : 0xa2,  # pressure sensitivity
        'off_t1'  : 0xa4,  # pressure offset
        'tcs'     : 0xa6,  # temp. coefficient of pressure sensitivity
        'tco'     : 0xa8,  # temp. coefficient of pressure offset
        't_ref'   : 0xaa,  # reference temp.
        'tempsens': 0xac   # temp. coefficient of the temp.
    }
    osr_conversion = {
        256 : {'command': partial(_adc_cmd, 0x40), 'msec': 0.6},
        512 : {'command': partial(_adc_cmd, 0x42), 'msec': 1.17},
        1024: {'command': partial(_adc_cmd, 0x44), 'msec': 2.28},
        2048: {'command': partial(_adc_cmd, 0x46), 'msec': 4.54},
        4096: {'command': partial(_adc_cmd, 0x48), 'msec': 9.04}
    }

    def __init__(self, address, oversampling_rate, port=1):
        assert address in [0x76, 0x77]
        super(BaseMS5803, self).__init__(address, oversampling_rate, port)
        self.send_reset()

    def send_reset(self):
        """Send reset command, then read and store coefficients from device
        permanent read-only memory (PROM).
        """
        self.write_byte(self.reset)
        time.sleep(0.1)
        self._read_prom()

    def _read_prom(self):
        """Read all the coefficients stored in device PROM, and store them as
        class attributes.
        """
        for coefficient, command in self.prom_coefficients.items():
            array = self.read_block_data(command, 2)
            value = self.array_block_to_unsigned_int(array)
            assert value > 0, "Error reading '{}' value.".format(coefficient)
            self.__setattr__(coefficient, value)

    def _read_raw_data(self, reading_type):
        """Send ADC command to device, wait for measurement, and read raw
        measurement.

        :param Reading reading_type: Temperature or pressure.
        :return int: 24-bit unsigned integer raw data reading from device.
        """
        delay = self.osr_conversion[self.oversampling_rate]['msec'] / 1000.0
        command = self.osr_conversion[self.oversampling_rate]['command']
        self.write_byte(command(reading_type))
        time.sleep(delay)
        array = self.read_block_data(self.read_adc, 3)
        return self.array_block_to_unsigned_int(array)

    def read_temperature(self):
        """
        return float: Temperature in degrees C.
        """
        raw_temperature = self._read_raw_data(Reading.TEMPERATURE)
        return self._convert_raw_temperature(raw_temperature)

    def read_temperature_and_pressure(self):
        """
        return tuple: Temperature in degrees C, pressure in mbar.
        """
        raw_temperature = self._read_raw_data(Reading.TEMPERATURE)
        raw_pressure = self._read_raw_data(Reading.PRESSURE)
        temperature = self._convert_raw_temperature(raw_temperature)
        pressure = self._convert_raw_pressure(raw_pressure)
        return temperature, pressure

    def read_pressure(self):
        """
        return float: Pressure in mbar.
        """
        _, pressure = self.read_temperature_and_pressure()
        return pressure

    @abstractmethod
    def _convert_raw_temperature(self, raw_temp_uint):
        pass

    @abstractmethod
    def _convert_raw_pressure(self, raw_pressure_uint):
        pass


class MS5803_01BA(BaseMS5803):
    """Concrete driver class for MS5803-01BA barometer."""
    reference_temp = 2000  # 20.00 C

    def __init__(self, address, oversampling_rate=4096, port=1):
        super(MS5803_01BA, self).__init__(address, oversampling_rate, port)

    def _convert_raw_temperature(self, raw_temp_uint):
        self.d_t = raw_temp_uint - (self.t_ref * 2**8)
        temp = int(self.reference_temp + (self.d_t * self.tempsens / 2**23))
        return self._second_order_temp_conversion(temp)

    def _second_order_temp_conversion(self, temp_estimate):
        very_low = -1500  # -15.00 C
        very_high = 4500  # 45.00 C
        t2 = off2 = sens2 = 0
        if temp_estimate >= self.reference_temp:
            if temp_estimate > very_high:
                sens2 -= int((temp_estimate - very_high)**2 / 2**3)
        else:
            t2 = int((self.d_t**2) / 2**31)
            off2 = int(3 * (temp_estimate - self.reference_temp)**2)
            sens2 = int(7 * (temp_estimate - self.reference_temp)**2 / 2**3)
            if temp_estimate < very_low:
                sens2 += 2 * (temp_estimate + 1500)**2
        self.off2 = off2
        self.sens2 = sens2
        return (temp_estimate - t2) / 100.0

    def _convert_raw_pressure(self, raw_pressure_uint):
        off = int((self.off_t1 * 2**16) + (self.tco * self.d_t / 2**7))
        off -= self.off2
        sens = int((self.sens_t1 * 2**15) + (self.tcs * self.d_t / 2**8))
        sens -= self.sens2
        pressure = int(((raw_pressure_uint * sens / 2**21) - off) / 2**15)
        return pressure / 100.0
