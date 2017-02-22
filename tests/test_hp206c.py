import pytest

from barometerdrivers import HP206C

try:
    from unittest.mock import call
except ImportError:
    from mock import call

READY = 0x40
NOT_READY = 0


def test_hp206c_init(i2c_mock_init, i2c_mock):
    i2c_mock.read_byte_data.side_effect = [READY]
    HP206C()

    i2c_mock_init.assert_called_once_with(0x76, 1)
    i2c_mock.write_byte.assert_called_once_with(0x06)
    i2c_mock.read_byte_data.assert_called_once_with(0x80 | 0x0d)


@pytest.fixture
def hp206c(i2c_mock):
    i2c_mock.read_byte_data.side_effect = [READY]
    barometer = HP206C()
    i2c_mock.write_byte.reset_mock()
    i2c_mock.read_byte_data.reset_mock()
    return barometer


def test_set_oversampling_rate_error(hp206c):
    with pytest.raises(ValueError) as e:
        hp206c.oversampling_rate = 555
    msg = e.value.args[0]
    assert msg.startswith("'555'")
    assert msg.endswith('Choose 128, 256, 512, 1024, 2048, 4096.')


def test_read_temperature_26C(i2c_mock, hp206c):
    i2c_mock.read_byte_data.side_effect = [READY]
    i2c_mock.read_block_data.side_effect = [[0x00, 0x0a, 0x5c]]

    assert hp206c.read_temperature() == 26.52
    i2c_mock.write_byte.assert_called_once_with(0x40 | 0x02)
    i2c_mock.read_byte_data.assert_called_once_with(0x80 | 0x0d)
    i2c_mock.read_block_data.assert_called_once_with(0x32, 3)


def test_read_temperature_n10C_with_ready_delay(i2c_mock, hp206c):
    i2c_mock.read_byte_data.side_effect = [NOT_READY, READY]
    i2c_mock.read_block_data.side_effect = [[0xff, 0xfc, 0x02]]

    assert hp206c.read_temperature() == -10.22
    i2c_mock.write_byte.assert_called_once_with(0x40 | 0x02)
    assert i2c_mock.read_byte_data.mock_calls == [call(0x80 | 0x0d)] * 2
    i2c_mock.read_block_data.assert_called_once_with(0x32, 3)


def test_read_pressure_1010mbar(i2c_mock, hp206c):
    i2c_mock.read_byte_data.side_effect = [READY]
    i2c_mock.read_block_data.side_effect = [[0x01, 0x8a, 0x9e]]

    assert hp206c.read_pressure() == 1010.22
    i2c_mock.write_byte.assert_called_once_with(0x40)
    i2c_mock.read_byte_data.assert_called_once_with(0x80 | 0x0d)
    i2c_mock.read_block_data.assert_called_once_with(0x30, 3)


def test_read_temperature_and_pressure_26C_1010mbar(i2c_mock, hp206c):
    i2c_mock.read_byte_data.side_effect = [READY]
    i2c_mock.read_block_data.side_effect = [
        [0x00, 0x0a, 0x5c, 0x01, 0x8a, 0x9e]
    ]

    assert hp206c.read_temperature_and_pressure() == (26.52, 1010.22)
    i2c_mock.write_byte.assert_called_once_with(0x40)
    i2c_mock.read_byte_data.assert_called_once_with(0x80 | 0x0d)
    i2c_mock.read_block_data.assert_called_once_with(0x10, 6)
