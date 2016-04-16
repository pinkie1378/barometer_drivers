class OneDKalman(object):
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
        self.kalman_gain = self.p_estimation_error / (self.p_estimation_error + self.r_measure_noise)
        self.x_value += self.kalman_gain * (measurement - self.x_value)
        self.p_estimation_error *= (1 - self.kalman_gain)
