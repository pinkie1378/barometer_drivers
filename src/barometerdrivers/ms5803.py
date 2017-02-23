import time
from abc import ABCMeta, abstractmethod
from functools import partial

from .absi2cbarometer import AbsI2CBarometer, OSRValue
from .util import array_block_to_unsigned_int


def _adc_cmd(pressure_cmd, is_pressure):
    """There are 2 ADCs, one for temperature and one for pressure. \
    The temperature commands have 1 extra bit.

    :param int pressure_cmd: Pressure ADC command bit.
    :param bool is_pressure: True for pressure, False for temperature.
    :return int: Correct command byte for reading temperature or pressure.
    """
    return pressure_cmd if is_pressure else pressure_cmd | 0x10


class AbsMS5803(AbsI2CBarometer):
    """Base class driver for reading temperature and pressure data \
    from the MS5803 family of barometers.
    """
    __metaclass__ = ABCMeta
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
        256 : OSRValue(partial(_adc_cmd, 0x40), 0.6),
        512 : OSRValue(partial(_adc_cmd, 0x42), 1.17),
        1024: OSRValue(partial(_adc_cmd, 0x44), 2.28),
        2048: OSRValue(partial(_adc_cmd, 0x46), 4.54),
        4096: OSRValue(partial(_adc_cmd, 0x48), 9.04)
    }

    def __init__(self, oversampling_rate, is_high_address, port):
        address = 0x77 if is_high_address else 0x76
        super(AbsMS5803, self).__init__(address, oversampling_rate, port)
        self.send_reset()

    def send_reset(self):
        """Send reset command, then read and store coefficients \
        from device permanent read-only memory (PROM).
        """
        self.i2c.write_byte(self.reset)
        time.sleep(0.1)
        self._read_prom()

    def _read_prom(self):
        """Read all the coefficients stored in device PROM, \
        and store them as attributes.
        """
        for coefficient, command in self.prom_coefficients.items():
            array = self.i2c.read_block_data(command, 2)
            value = array_block_to_unsigned_int(array)
            assert value > 0, "Error reading '{}' value.".format(coefficient)
            self.__setattr__(coefficient, value)

    def _read_raw_data(self, is_pressure):
        """Send ADC command to device, wait for measurement, \
        and read raw measurement.

        :param bool is_pressure: True for pressure, False for temperature.
        :return int: 24-bit unsigned integer raw data reading from device.
        """
        osr_value = self.osr_conversion[self.oversampling_rate]
        delay = osr_value.msec / 1000.0
        command = osr_value.command(is_pressure)
        self.i2c.write_byte(command)
        time.sleep(delay)
        array = self.i2c.read_block_data(self.read_adc, 3)
        return array_block_to_unsigned_int(array)

    def read_temperature(self):
        """
        return float: Temperature in degrees C.
        """
        raw_temperature = self._read_raw_data(is_pressure=False)
        return self._convert_raw_temperature(raw_temperature)

    def read_temperature_and_pressure(self):
        """
        return tuple: Temperature in degrees C, pressure in mbar.
        """
        raw_temperature = self._read_raw_data(is_pressure=False)
        raw_pressure = self._read_raw_data(is_pressure=True)
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
        pass  # pragma: no cover

    @abstractmethod
    def _convert_raw_pressure(self, raw_pressure_uint):
        pass  # pragma: no cover


class MS5803_01BA(AbsMS5803):
    """Concrete driver class for MS5803-01BA barometer."""
    reference_temp = 2000  # 20.00 C

    def __init__(self, oversampling_rate=1024, is_high_address=True, port=1):
        super(MS5803_01BA, self).__init__(oversampling_rate,
                                          is_high_address,
                                          port)

    def _convert_raw_temperature(self, raw_temp_uint):
        self.d_t = raw_temp_uint - (self.t_ref * 2**8)
        temp = self.reference_temp + (1.0 * self.d_t * self.tempsens / 2**23)
        return self._second_order_temp_conversion(temp)

    def _second_order_temp_conversion(self, temp_estimate):
        very_low = -1500  # -15.00 C
        very_high = 4500  # 45.00 C
        t2 = off2 = sens2 = 0
        if temp_estimate >= self.reference_temp:
            if temp_estimate > very_high:
                sens2 -= 1.0 * (temp_estimate - very_high)**2 / 2**3
        else:
            t2 = 1.0 * self.d_t**2 / 2**31
            off2 = 3.0 * (temp_estimate - self.reference_temp)**2
            sens2 = 7.0 * (temp_estimate - self.reference_temp)**2 / 2**3
            if temp_estimate < very_low:
                sens2 += 2.0 * (temp_estimate + 1500)**2
        self.off2 = off2
        self.sens2 = sens2
        return int(temp_estimate - t2) / 100.0

    def _convert_raw_pressure(self, raw_pressure_uint):
        off = (self.off_t1 * 2**16) + (1.0 * self.tco * self.d_t / 2**7)
        off -= self.off2
        sens = (self.sens_t1 * 2**15) + (1.0 * self.tcs * self.d_t / 2**8)
        sens -= self.sens2
        pressure = ((raw_pressure_uint * sens / 2**21) - off) / 2**15
        return int(pressure) / 100.0
