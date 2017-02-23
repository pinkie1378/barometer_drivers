from pytest import fixture

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


@fixture
def i2c_mock_init():
    mock = patch('barometerdrivers.absi2cbarometer.I2CReadWrite')
    mock_session = mock.start()
    yield mock_session
    mock_session.stop()


@fixture
def i2c_mock(i2c_mock_init):
    return i2c_mock_init.return_value
