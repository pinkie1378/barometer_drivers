from abc import ABCMeta
import math


class AbstractSmoother(object):
    """Interface for data smoothing classes."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self, measurement):
        """
        :param float measurement: Latest measurement to add to smoothing model.
        """
        pass

    @abstractmethod
    def value(self):
        """
        :return float: Current true reading estimated by smoothing model.
        """
        pass


class AbstractRollingSmoother(AbstractSmoother):
    """Base class for using rolling algorithms to smooth data."""
    __metaclass__ = ABCMeta

    def __init__(self, init_value, length):
        self.values = [init_value]
        self.length = length
        self.index = 0
        self.full = False

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

    def __init__(self, init_value, length):
        super(RollingRootMeanSquare, self).__init__(init_value, length)

    @property
    def value(self):
        return sum(self.values) / len(self.values)


class RollingRootMeanSquare(AbstractRollingSmoother):
    """Use the root mean square of measurements to estimate true value."""

    def __init__(self, init_value, length):
        super(RollingRootMeanSquare, self).__init__(init_value, length)

    @property
    def value(self):
        squares = [x ** 2 for x in self.values]
        return math.sqrt(sum(squares) / len(self.values))


class OneDKalman(AbstractSmoother):
    """Use for smoothing out noisy sensor outputs. Adapted from:
    http://interactive-matter.eu/blog/2009/12/18/filtering-sensor-data-with-a-kalman-filter/
    """
    def __init__(self, q_process_noise,
                 r_measure_noise,
                 p_estimation_error,
                 x_init_value):
        self.q_process_noise = q_process_noise
        self.r_measure_noise = r_measure_noise
        self.p_estimation_error = p_estimation_error
        self.x_value = x_init_value

    def update(self, measurement):
        # prediction update
        self.p_estimation_error += self.q_process_noise

        # measurement update
        self.kalman_gain = self.p_estimation_error / (
            self.p_estimation_error + self.r_measure_noise)
        self.x_value += self.kalman_gain * (measurement - self.x_value)
        self.p_estimation_error *= (1 - self.kalman_gain)

    @property
    def value(self):
        return self.x_value
