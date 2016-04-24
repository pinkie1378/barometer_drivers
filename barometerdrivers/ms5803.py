from enum import Enum
from functools import partial
import time

from .basebarometer import BaseBarometer


class Reading(Enum):
    TEMPERATURE = 't'
    PRESSURE = 'p'


def _osr_cmd(pressure_cmd, reading_type):
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


class MS5803_01BA(BaseBarometer):
    """Driver for reading temperature and pressure data from MS5803-01BA."""
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
        256 : {'command': partial(_osr_cmd, 0x40), 'msec': 0.6},
        512 : {'command': partial(_osr_cmd, 0x42), 'msec': 1.17},
        1024: {'command': partial(_osr_cmd, 0x44), 'msec': 2.28},
        2048: {'command': partial(_osr_cmd, 0x46), 'msec': 4.54},
        4096: {'command': partial(_osr_cmd, 0x50), 'msec': 9.04}
    }

    def __init__(self, address, oversampling_rate=4096, port=1):
        assert address in [0x76, 0x77]
        super(MS5803_01BA, self).__init__(address, oversampling_rate, port)
        self.send_reset()

    def send_reset(self):
        self.write_byte(self.reset)
        self._read_prom()

    def _read_prom(self):
        for coefficient, command in self.prom_coefficients.items():
            array = self.read_block_data(command, 2)
            value = self.array_block_to_unsigned_int(array)
            assert value > 0, "Error reading '{}' value.".format(coefficient)
            self.__setattr__(coefficient, value)

    def _read_raw_data(self, reading_type):
        delay = self.osr_conversion[self.oversampling_rate]['msec'] / 1000.0
        command = self.osr_conversion[self.oversampling_rate]['command']
        self.write_byte(command(reading_type))
        time.sleep(delay)
        array = self.read_block_data(self.read_adc, 3)
        return self.array_block_to_unsigned_int(array)

    def read_temperature(self):
        raw_temperature = self._read_raw_data(Reading.TEMPERATURE)
        return self._convert_raw_temperature(raw_temperature)

    def read_temperature_and_pressure(self):
        raw_temperature = self._read_raw_data(Reading.TEMPERATURE)
        raw_pressure = self._read_raw_data(Reading.PRESSURE)
        temperature = self._convert_raw_temperature(raw_temperature)
        pressure = self._convert_raw_pressure(raw_pressure)
        return temperature, pressure

    def read_pressure(self):
        _, pressure = self.read_temperature_and_pressure()
        return pressure

    def _convert_raw_temperature(self, raw_temp_uint):
        return None

    def _convert_raw_pressure(self, raw_pressure_uint):
        return None
