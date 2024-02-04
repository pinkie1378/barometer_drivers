import math
from abc import ABCMeta, abstractmethod


class AbstractSmoother(object):
    """Interface for data smoothing classes."""

    __metaclass__ = ABCMeta

    def __init__(self, decimal_places):
        assert isinstance(decimal_places, int)
        self.decimal_places = decimal_places

    @abstractmethod
    def update(self, measurement):
        """
        :param float measurement: Latest measurement to add to smoothing model.
        """
        pass  # pragma: no cover

    @abstractmethod
    def value(self):
        """
        :return float: Current true reading estimated by smoothing model.
        """
        pass  # pragma: no cover


class AbstractRollingSmoother(AbstractSmoother):
    """Base class for using rolling algorithms to smooth data."""

    __metaclass__ = ABCMeta

    def __init__(self, init_value, length, decimal_places):
        super(AbstractRollingSmoother, self).__init__(decimal_places)
        self.values = [init_value]
        assert isinstance(length, int) and length > 0
        self.length = length
        self.index = 0
        self.full = False if length > 1 else True

    def update(self, measurement):
        if self.full:
            self.values[self.index] = measurement
            self.index += 1
            if self.index == self.length:
                self.index = 0
        else:
            self.values.append(measurement)
            if len(self.values) == self.length:
                self.full = True


class RollingMean(AbstractRollingSmoother):
    """Use the mean of measurements to estimate true value."""

    def __init__(self, init_value, length, decimal_places):
        super(RollingMean, self).__init__(init_value, length, decimal_places)

    @property
    def value(self):
        return round(sum(self.values) / len(self.values), self.decimal_places)


class RollingRootMeanSquared(AbstractRollingSmoother):
    """Use the root mean squared of measurements to estimate true value."""

    def __init__(self, init_value, length, decimal_places):
        super(RollingRootMeanSquared, self).__init__(init_value, length, decimal_places)

    @property
    def value(self):
        squares = [x**2 for x in self.values]
        return round(math.sqrt(sum(squares) / len(self.values)), self.decimal_places)


class OneDKalman(AbstractSmoother):
    """Use for smoothing out noisy sensor outputs. Adapted from:
    http://interactive-matter.eu/blog/2009/12/18/filtering-sensor-data-with-a-kalman-filter/
    """

    def __init__(
        self,
        x_init_value,
        p_estimation_error,
        q_process_noise,
        r_measure_noise,
        decimal_places,
    ):
        super(OneDKalman, self).__init__(decimal_places)
        self.x_value = float(x_init_value)
        self.p_estimation_error = float(p_estimation_error)
        self.q_process_noise = float(q_process_noise)
        self.r_measure_noise = float(r_measure_noise)

    def update(self, measurement):
        # prediction update
        self.p_estimation_error += self.q_process_noise

        # measurement update
        self.kalman_gain = self.p_estimation_error / (
            self.p_estimation_error + self.r_measure_noise
        )
        self.x_value += self.kalman_gain * (measurement - self.x_value)
        self.p_estimation_error *= 1 - self.kalman_gain

    @property
    def value(self):
        return round(self.x_value, self.decimal_places)
