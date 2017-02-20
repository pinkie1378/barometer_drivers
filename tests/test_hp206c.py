import pytest

from barometerdrivers import HP206C
from barometerdrivers.basei2c import BaseI2CDriver as I2C

try:
    from unittest.mock import patch, call
except ImportError:
    from mock import patch, call


@pytest.fixture(scope='module')
@patch.object(I2C, '__init__')
@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_byte_data', side_effect=[0x40])
def hp206c(read_mock, write_mock, init_mock):
    barometer = HP206C()

    init_mock.assert_called_once_with(0x76, 1)
    write_mock.assert_called_once_with(0x06)
    read_mock.assert_called_once_with(0x80 | 0x0d)

    return barometer


def test_set_oversampling_rate_error(hp206c):
    with pytest.raises(ValueError) as e:
        hp206c.oversampling_rate = 555
    msg = e.value.args[0]
    assert msg.startswith("'555'")
    assert msg.endswith('Choose 128, 256, 512, 1024, 2048, 4096.')


@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_byte_data', side_effect=[0x40])
@patch.object(I2C, 'read_block_data', side_effect=[[0x00, 0x0a, 0x5c]])
def test_read_temperature_26C(read_block_mock, read_mock, write_mock, hp206c):
    assert hp206c.read_temperature() == 26.52
    write_mock.assert_called_once_with(0x40 | 0x02)
    read_mock.assert_called_once_with(0x80 | 0x0d)
    read_block_mock.assert_called_once_with(0x32, 3)


@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_byte_data', side_effect=[0x00, 0x40])
@patch.object(I2C, 'read_block_data', side_effect=[[0xff, 0xfc, 0x02]])
def test_read_temperature_n10C(read_block_mock, read_mock, write_mock, hp206c):
    assert hp206c.read_temperature() == -10.22
    write_mock.assert_called_once_with(0x40 | 0x02)
    assert read_mock.call_args_list == [call(0x80 | 0x0d)] * 2
    read_block_mock.assert_called_once_with(0x32, 3)


@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_byte_data', side_effect=[0x40])
@patch.object(I2C, 'read_block_data', side_effect=[[0x01, 0x8a, 0x9e]])
def test_read_pressure_1010mbar(
        read_block_mock, read_mock, write_mock, hp206c):
    assert hp206c.read_pressure() == 1010.22
    write_mock.assert_called_once_with(0x40)
    read_mock.assert_called_once_with(0x80 | 0x0d)
    read_block_mock.assert_called_once_with(0x30, 3)


@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_byte_data', side_effect=[0x40])
@patch.object(I2C, 'read_block_data', side_effect=[
    [0x00, 0x0a, 0x5c, 0x01, 0x8a, 0x9e]
])
def test_read_temperature_and_pressure_26C_1010mbar(
        read_block_mock, read_mock, write_mock, hp206c):
    assert hp206c.read_temperature_and_pressure() == (26.52, 1010.22)
    write_mock.assert_called_once_with(0x40)
    read_mock.assert_called_once_with(0x80 | 0x0d)
    read_block_mock.assert_called_once_with(0x10, 6)
