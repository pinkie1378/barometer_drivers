from .absms5803 import AbsMS5803


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
        return self.__second_order_temp_conversion(temp)

    def __second_order_temp_conversion(self, temp_estimate):
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
