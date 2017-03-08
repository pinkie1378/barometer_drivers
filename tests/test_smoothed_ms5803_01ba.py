import time

from pytest import fixture

from barometerdrivers.smooth import SmoothedMS5803_01BA

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


@fixture
def mock_ms5803_01ba_init():
    mock = patch('barometerdrivers.smooth.ms5803smoother.MS5803_01BA')
    mock_session = mock.start()
    yield mock_session
    mock_session.stop()


def test_smoothed_ms5803_01ba_init(mock_ms5803_01ba_init):
    SmoothedMS5803_01BA(True)
    mock_ms5803_01ba_init.assert_called_once_with(oversampling_rate=1024,
                                                  is_high_address=True,
                                                  port=1)


@fixture
def mock_ms5803_01ba(mock_ms5803_01ba_init):
    driver = mock_ms5803_01ba_init.return_value
    driver.read_temperature_and_pressure.side_effect = lambda: (20.0, 1000.0)
    driver.read_temperature.side_effect = lambda: 20.0
    driver.read_pressure.side_effect = lambda: 1000.0
    return driver


@fixture
def mock_smooth(mock_ms5803_01ba):
    return SmoothedMS5803_01BA(True)


def test_smoothed_ms5803_01ba_temperature(mock_ms5803_01ba, mock_smooth):
    start = time.time()
    temperature = mock_smooth.temperature
    end = time.time() - start

    assert temperature == 20.0
    assert 0.25 <= end <= 0.27  # sensor should be polled for 0.25 sec
    assert mock_ms5803_01ba.read_temperature_and_pressure.called
    assert mock_ms5803_01ba.read_temperature.called
    assert not mock_ms5803_01ba.read_pressure.called


def test_smoothed_ms5803_01ba_pressure(mock_ms5803_01ba, mock_smooth):
    start = time.time()
    pressure = mock_smooth.pressure
    end = time.time() - start

    assert pressure == 1000.0
    assert 0.25 <= end <= 0.27  # sensor should be polled for 0.25 sec
    assert mock_ms5803_01ba.read_temperature_and_pressure.called
    assert not mock_ms5803_01ba.read_temperature.called
    assert mock_ms5803_01ba.read_pressure.called


def test_smoothed_ms5803_01ba_temp_pressure(mock_ms5803_01ba, mock_smooth):
    start = time.time()
    temperature, pressure = mock_smooth.temperature_and_pressure
    end = time.time() - start

    assert temperature == 20.0
    assert pressure == 1000.0
    assert 0.25 <= end <= 0.27  # sensor should be polled for 0.25 sec
    assert mock_ms5803_01ba.read_temperature_and_pressure.called
    assert not mock_ms5803_01ba.read_temperature.called
    assert not mock_ms5803_01ba.read_pressure.called
