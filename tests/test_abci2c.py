import pytest

from drivers.abci2c import BaseI2CDriver


@pytest.mark.parametrize('byte_array, int_value', [
    ([0x00, 0x0a, 0x5c], 2652),
    ([0xff, 0xfc, 0x02], -1022),
    ([0x01, 0x8a, 0x9e], 101022)
])
def test_array_block_to_value(byte_array, int_value):
    assert BaseI2CDriver.array_block_to_value(byte_array) == int_value


@pytest.mark.parametrize('twos_compliment, bits, int_value', [
    (16772216, 24, -5000), (5000, 24, 5000)
])
def test_twos_compliment_to_signed_int(twos_compliment, bits, int_value):
    value = BaseI2CDriver.twos_compliment_to_signed_int(twos_compliment, bits)
    assert value == int_value
