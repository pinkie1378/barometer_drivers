import time

import pytest

from barometerdrivers.smooth import SmoothedMS5803_01BA

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


@pytest.fixture
@patch('barometerdrivers.smooth.ms5803smoother.MS5803_01BA')
def mocked_smoothed_ms5803_01ba(driver_mock):
    smooth = SmoothedMS5803_01BA(0x77)
    driver_mock.assert_called_once_with(0x77, oversampling_rate=1024, port=1)

    driver = driver_mock.return_value
    driver.read_temperature_and_pressure.side_effect = lambda: (20.0, 1000.0)
    driver.read_temperature.side_effect = lambda: 20.0
    driver.read_pressure.side_effect = lambda: 1000.0

    return driver, smooth


def test_smoothed_ms5803_01ba_temperature(mocked_smoothed_ms5803_01ba):
    mock_ms5803, smooth = mocked_smoothed_ms5803_01ba
    start = time.time()
    temperature = smooth.temperature
    end = time.time() - start

    assert temperature == 20.0
    assert 0.25 <= end <= 0.27  # sensor should be polled for 0.25 sec
    assert mock_ms5803.read_temperature_and_pressure.called
    assert mock_ms5803.read_temperature.called
    assert not mock_ms5803.read_pressure.called


def test_smoothed_ms5803_01ba_pressure(mocked_smoothed_ms5803_01ba):
    mock_ms5803, smooth = mocked_smoothed_ms5803_01ba
    start = time.time()
    pressure = smooth.pressure
    end = time.time() - start

    assert pressure == 1000.0
    assert 0.25 <= end <= 0.27  # sensor should be polled for 0.25 sec
    assert mock_ms5803.read_temperature_and_pressure.called
    assert not mock_ms5803.read_temperature.called
    assert mock_ms5803.read_pressure.called


def test_smoothed_ms5803_01ba_temp_pressure(mocked_smoothed_ms5803_01ba):
    mock_ms5803, smooth = mocked_smoothed_ms5803_01ba
    start = time.time()
    temperature, pressure = smooth.temperature_and_pressure
    end = time.time() - start

    assert temperature == 20.0
    assert pressure == 1000.0
    assert 0.25 <= end <= 0.27  # sensor should be polled for 0.25 sec
    assert mock_ms5803.read_temperature_and_pressure.called
    assert not mock_ms5803.read_temperature.called
    assert not mock_ms5803.read_pressure.called
