import pytest
import smbus

from barometerdrivers.i2creadwrite import I2CReadWrite

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

ADDRESS = 0x13


@pytest.fixture(scope="module")
@patch.object(smbus.SMBus, "open")
def i2c_driver(open_mock):
    port = 0
    driver = I2CReadWrite(ADDRESS, port)
    open_mock.assert_called_once_with(port)
    return driver


@patch.object(smbus.SMBus, "write_byte")
def test_write_byte(write_mock, i2c_driver):
    i2c_driver.write_byte(0x99)
    write_mock.assert_called_once_with(ADDRESS, 0x99)


@patch.object(smbus.SMBus, "read_byte_data", side_effect=[0x12])
def test_read_byte_data(read_mock, i2c_driver):
    byte = i2c_driver.read_byte_data(0x99)
    read_mock.assert_called_once_with(ADDRESS, 0x99)
    assert byte == 0x12


@patch.object(smbus.SMBus, "read_i2c_block_data", side_effect=[[1, 2, 3]])
def test_read_block_data(read_mock, i2c_driver):
    byte_array = i2c_driver.read_block_data(0x99, 3)
    read_mock.assert_called_once_with(ADDRESS, 0x99, 3)
    assert byte_array == [1, 2, 3]


def test_write_byte_bad_command(i2c_driver):
    with pytest.raises(ValueError) as e:
        i2c_driver.write_byte(-1)
    msg = e.value.args[0]
    assert msg == "'-1' is not an unsigned byte."


def test_read_byte_data_bad_command(i2c_driver):
    with pytest.raises(ValueError) as e:
        i2c_driver.read_byte_data(1.23)
    msg = e.value.args[0]
    assert msg == "'1.23' is not an unsigned byte."


def test_read_block_data_bad_command(i2c_driver):
    with pytest.raises(ValueError) as e:
        i2c_driver.read_block_data(0x100, 1)
    msg = e.value.args[0]
    assert msg == "'256' is not an unsigned byte."
