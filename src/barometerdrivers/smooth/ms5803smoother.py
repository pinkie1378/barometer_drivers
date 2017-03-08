import time

from ..ms5803_01ba import MS5803_01BA
from .smoothalgorithms import OneDKalman


class SmoothedMS5803_01BA(object):
    """Polls MS5803-01BA sensor and returns pressure and/or temperature values
    obtained from proccessing readings with :class:`OneDKalman`. Ignores data
    from the first 100 ms, as my experiments show these readings can be noisy.
    Readings from 100 - 250 ms are processed with the Kalman filter, and the
    adjusted values are returned.
    """
    ignore_sec = 0.1
    poll_sec = 0.25

    def __init__(self, is_high_address, port=1):
        self.ms5803 = MS5803_01BA(oversampling_rate=1024,
                                  is_high_address=is_high_address,
                                  port=port)

    def _discard_first_100_msec(self, start):
        temperature = pressure = None
        while time.time() < start + self.ignore_sec:
            temperature, pressure = self.ms5803.read_temperature_and_pressure()
        return temperature, pressure

    @property
    def temperature(self):
        """
        :return float: Temperature in degrees C processed via Kalman filter.
        """
        start = time.time()
        init_temp, _ = self._discard_first_100_msec(start)
        smooth_temp = OneDKalman(init_temp, 4, 0.0625, 4, 2)
        while time.time() < start + self.poll_sec:
            smooth_temp.update(self.ms5803.read_temperature())
        return smooth_temp.value

    @property
    def pressure(self):
        """
        :return float: Pressure in mbar processed via Kalman filter.
        """
        start = time.time()
        _, init_pressure = self._discard_first_100_msec(start)
        smooth_pressure = OneDKalman(init_pressure, 4, 0.0625, 4, 2)
        while time.time() < start + self.poll_sec:
            smooth_pressure.update(self.ms5803.read_pressure())
        return smooth_pressure.value

    @property
    def temperature_and_pressure(self):
        """
        :return tuple: Temperature in degrees C, pressure in mbar processed
         via Kalman filter.
        """
        start = time.time()
        init_temp, init_pressure = self._discard_first_100_msec(start)
        smooth_temp = OneDKalman(init_temp, 4, 0.0625, 4, 2)
        smooth_pressure = OneDKalman(init_pressure, 4, 0.0625, 4, 2)
        while time.time() < start + self.poll_sec:
            temperature, pressure = self.ms5803.read_temperature_and_pressure()
            smooth_temp.update(temperature)
            smooth_pressure.update(pressure)
        return smooth_temp.value, smooth_pressure.value
