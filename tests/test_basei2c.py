import pytest

from drivers.basei2c import BaseI2CDriver


@pytest.mark.parametrize('byte_array, expected', [
    ([0x00, 0x0a, 0x5c], 2652),
    ([0xff, 0xfc, 0x02], -1022),
    ([0x01, 0x8a, 0x9e], 101022)
])
def test_array_block_to_value(byte_array, expected):
    assert BaseI2CDriver.array_block_to_value(byte_array) == expected


@pytest.mark.parametrize('twos_compliment, bits, expected', [
    (16772216, 24, -5000), (5000, 24, 5000)
])
def test_twos_compliment_to_signed_int(twos_compliment, bits, expected):
    value = BaseI2CDriver.twos_compliment_to_signed_int(twos_compliment, bits)
    assert value == expected


@pytest.mark.parametrize('byte, expected', [
    (-0x01, False), (0x00, True), (0x9e, True), (0xff, True), (0x100, False)
])
def test_is_unsigned_byte(byte, expected):
    assert BaseI2CDriver.is_unsigned_byte(byte) == expected


@pytest.mark.parametrize('val1, val2, args, expected', [
    (0b101, 0b010, [], 0b111), (0b101, 0b111, [], 0b111),
    (0x00, 0x00, [0xec], 0xec), (1, 2, [4, 8, 16], 31)
])
def test_do_bitwise_or(val1, val2, args, expected):
    assert BaseI2CDriver.do_bitwise_or(val1, val2, *args) == expected
