import pytest

import barometerdrivers.smooth.smoothalgorithms as smooth


initial_value = 1.0
measured_values = [2.0, 3.0, 4.0, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0]


@pytest.mark.parametrize(
    "smoother_class, length, decimal_places, expected",
    [
        (smooth.RollingMean, 1, 0, measured_values),
        (smooth.RollingMean, 3, 0, [2.0, 2.0, 3.0, 4.0, 3.0, 3.0, 2.0, 3.0, 4.0]),
        (smooth.RollingMean, 3, 3, [1.5, 2.0, 3.0, 4.0, 3.333, 2.667, 2.0, 3.0, 4.0]),
        (
            smooth.RollingMean,
            10,
            3,
            [1.5, 2.0, 2.5, 3.0, 2.667, 2.571, 2.625, 2.778, 3.0],
        ),
        (smooth.RollingRootMeanSquared, 1, 0, measured_values),
        (
            smooth.RollingRootMeanSquared,
            3,
            0,
            [2.0, 2.0, 3.0, 4.0, 4.0, 3.0, 2.0, 3.0, 4.0],
        ),
        (
            smooth.RollingRootMeanSquared,
            3,
            3,
            [1.581, 2.16, 3.109, 4.082, 3.742, 3.162, 2.16, 3.109, 4.082],
        ),
        (
            smooth.RollingRootMeanSquared,
            10,
            3,
            [1.581, 2.16, 2.739, 3.317, 3.055, 2.928, 2.937, 3.073, 3.317],
        ),
    ],
)
def test_rolling_smoothers(smoother_class, length, decimal_places, expected):
    smoother = smoother_class(initial_value, length, decimal_places)
    assert smoother.value == initial_value
    for measure, expect in zip(measured_values, expected):
        smoother.update(measure)
        assert smoother.value == expect


@pytest.mark.parametrize(
    "q_process_noise, r_measure_noise, expected",
    [
        # neutral
        (1, 1, [1.8, 2.57, 3.46, 4.41, 2.3, 2.12, 2.66, 3.49, 4.42]),
        # high q, minimal smoothing
        (5, 1, [1.89, 2.84, 3.83, 4.83, 1.56, 1.94, 2.84, 3.83, 4.83]),
        # low r, minimal smoothing
        (1, 0.2, [1.95, 2.85, 3.83, 4.83, 1.56, 1.94, 2.84, 3.83, 4.83]),
        # high q and low r, least smoothing
        (5, 0.2, [1.98, 2.96, 3.96, 4.96, 1.15, 1.97, 2.96, 3.96, 4.96]),
        # high r, more smoothing
        (1, 5, [1.44, 2.05, 2.78, 3.59, 2.65, 2.42, 2.63, 3.12, 3.79]),
        # low q, more smoothing
        (0.2, 1, [1.76, 2.37, 3.04, 3.78, 2.76, 2.49, 2.67, 3.15, 3.81]),
        # low q and high r, most smoothing
        (0.2, 5, [1.39, 1.87, 2.41, 3.0, 2.58, 2.46, 2.57, 2.84, 3.24]),
    ],
)
def test_one_d_kalman(q_process_noise, r_measure_noise, expected):
    kalman_params = {
        "x_init_value": initial_value,
        "p_estimation_error": 3,
        "q_process_noise": q_process_noise,
        "r_measure_noise": r_measure_noise,
        "decimal_places": 2,
    }
    smoother = smooth.OneDKalman(**kalman_params)
    assert smoother.value == initial_value
    for measure, expect in zip(measured_values, expected):
        smoother.update(measure)
        assert smoother.value == expect
