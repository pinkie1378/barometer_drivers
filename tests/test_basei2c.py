import pytest
import six
import smbus

from barometerdrivers.basei2c import BaseI2CDriver

if six.PY2:
    import mock
else:
    import unittest.mock as mock


@pytest.mark.parametrize('byte_array, expected', [
    ([0x00, 0x0a, 0x5c], 2652),
    ([0xff, 0xfc, 0x02], 16776194),
    ([0x01, 0x8a, 0x9e], 101022)
])
def test_array_block_to_unsigned_int(byte_array, expected):
    assert BaseI2CDriver.array_block_to_unsigned_int(byte_array) == expected


@pytest.mark.parametrize('byte_array, bad_value, index', [
    ([-0x01, 0x00, 0xff], -0x01, 0),
    ([0x00, 1.234, 0xff], 1.234, 1),
    ([0x00, 0xff, 0x100], 0x100, 2)
])
def test_array_block_to_unsigned_int_1_bad_value(byte_array, bad_value, index):
    with pytest.raises(ValueError) as e:
        BaseI2CDriver.array_block_to_unsigned_int(byte_array)
    msg = e.value.args[0]
    assert msg.startswith("Value '{}' at index '{}'".format(bad_value, index))


def test_array_block_to_unsigned_int_multiple_bad_values():
    bad_byte_array = [-0x01, 1.234, 0x100]
    with pytest.raises(ValueError) as e:
        BaseI2CDriver.array_block_to_unsigned_int(bad_byte_array)
    msg = e.value.args[0]
    assert msg.startswith('Values [-1, 1.234, 256] at indeces [0, 1, 2]')


@pytest.mark.parametrize('byte_array, expected', [
    ([0x00, 0x0a, 0x5c], 2652),
    ([0xff, 0xfc, 0x02], -1022),
    ([0x01, 0x8a, 0x9e], 101022)
])
def test_array_block_to_int(byte_array, expected):
    assert BaseI2CDriver.array_block_to_int(byte_array) == expected


@pytest.mark.parametrize('twos_compliment, bits, expected', [
    (16772216, 24, -5000), (5000, 24, 5000)
])
def test_twos_compliment_to_signed_int(twos_compliment, bits, expected):
    value = BaseI2CDriver.twos_compliment_to_signed_int(twos_compliment, bits)
    assert value == expected


@pytest.mark.parametrize('byte, expected', [
    (0x00, True), (0x9e, True), (0xff, True),
    (-0x01, False), (12.3, False), (0x100, False)
])
def test_is_unsigned_byte(byte, expected):
    assert BaseI2CDriver.is_unsigned_byte(byte) == expected


@pytest.mark.parametrize('val1, val2, args, expected', [
    (0b101, 0b010, [], 0b111), (0b101, 0b111, [], 0b111),
    (0x00, 0x00, [0xec], 0xec), (1, 2, [4, 8, 16], 31)
])
def test_do_bitwise_or(val1, val2, args, expected):
    assert BaseI2CDriver.do_bitwise_or(val1, val2, *args) == expected


@pytest.mark.parametrize('value, index, expected', [
    (0, 0, False), (1, 0, True), (2, 0, False),
    (1, 1, False), (2, 1, True), (3, 1, True),
    (63, 6, False), (64, 6, True), (127, 6, True), (128, 6, False)
])
def test_is_bit_set(value, index, expected):
    assert BaseI2CDriver.is_bit_set(value, index) == expected


@pytest.mark.parametrize('invalid_value', [-1, 3.14])
def test_is_bit_set_invalid_value(invalid_value):
    with pytest.raises(ValueError) as e:
        BaseI2CDriver.is_bit_set(invalid_value, 0)
    msg = e.value.args[0]
    assert msg.startswith("Invalid parameter '{}'.".format(invalid_value))


address = 0x13


@pytest.fixture(scope='module')
def i2c_driver(request):
    with mock.patch.object(smbus.SMBus, 'open') as open_mock:
        port = 0
        driver = BaseI2CDriver(address, port)
        open_mock.assert_called_once_with(port)
    return driver


@mock.patch.object(smbus.SMBus, 'write_byte')
def test_write_byte(write_mock, i2c_driver):
    i2c_driver.write_byte(0x99)
    write_mock.assert_called_once_with(address, 0x99)


@mock.patch.object(smbus.SMBus, 'read_byte_data', side_effect=[0x12])
def test_read_byte_data(read_mock, i2c_driver):
    byte = i2c_driver.read_byte_data(0x99)
    read_mock.assert_called_once_with(address, 0x99)
    assert byte == 0x12


@mock.patch.object(smbus.SMBus, 'read_i2c_block_data', side_effect=[[1, 2, 3]])
def test_read_block_data(read_mock, i2c_driver):
    byte_array = i2c_driver.read_block_data(0x99, 3)
    read_mock.assert_called_once_with(address, 0x99, 3)
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
