import pytest

import barometerdrivers.smooth.smoothalgorithms as smooth


initial_value = 1.0
measured_values = [2.0, 3.0, 4.0, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0]


@pytest.mark.parametrize('smoother_class, length, decimal_places, expected', [
    (smooth.RollingMean, 1, 0, measured_values),
    (smooth.RollingMean, 3, 0,
        [2.0, 2.0, 3.0, 4.0, 3.0, 3.0, 2.0, 3.0, 4.0]),
    (smooth.RollingMean, 3, 3,
        [1.5, 2.0, 3.0, 4.0, 3.333, 2.667, 2.0, 3.0, 4.0]),
    (smooth.RollingMean, 10, 3,
        [1.5, 2.0, 2.5, 3.0, 2.667, 2.571, 2.625, 2.778, 3.0]),
    (smooth.RollingRootMeanSquared, 1, 0, measured_values),
    (smooth.RollingRootMeanSquared, 3, 0,
        [2.0, 2.0, 3.0, 4.0, 4.0, 3.0, 2.0, 3.0, 4.0]),
    (smooth.RollingRootMeanSquared, 3, 3,
        [1.581, 2.16, 3.109, 4.082, 3.742, 3.162, 2.16, 3.109, 4.082]),
    (smooth.RollingRootMeanSquared, 10, 3,
        [1.581, 2.16, 2.739, 3.317, 3.055, 2.928, 2.937, 3.073, 3.317])
])
def test_rolling_smoothers(smoother_class, length, decimal_places, expected):
    smoother = smoother_class(initial_value, length, decimal_places)
    assert smoother.value == initial_value
    for measure, expect in zip(measured_values, expected):
        smoother.update(measure)
        assert smoother.value == expect
