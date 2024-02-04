import pytest

from barometerdrivers.helpers.util import (
    array_block_to_signed_int,
    array_block_to_unsigned_int,
    do_bitwise_or,
    is_bit_set,
    is_unsigned_byte,
    twos_compliment_to_signed_int,
)


@pytest.mark.parametrize(
    "val1, val2, args, expected",
    [
        (0b101, 0b010, [], 0b111),
        (0b101, 0b111, [], 0b111),
        (0x00, 0x00, [0xEC], 0xEC),
        (1, 2, [4, 8, 16], 31),
    ],
)
def test_do_bitwise_or(val1, val2, args, expected):
    assert do_bitwise_or(val1, val2, *args) == expected


@pytest.mark.parametrize(
    "byte, expected",
    [
        (0x00, True),
        (0x9E, True),
        (0xFF, True),
        (-0x01, False),
        (12.3, False),
        (0x100, False),
    ],
)
def test_is_unsigned_byte(byte, expected):
    assert is_unsigned_byte(byte) == expected


@pytest.mark.parametrize(
    "value, index, expected",
    [
        (0, 0, False),
        (1, 0, True),
        (2, 0, False),
        (1, 1, False),
        (2, 1, True),
        (3, 1, True),
        (63, 6, False),
        (64, 6, True),
        (127, 6, True),
        (128, 6, False),
    ],
)
def test_is_bit_set(value, index, expected):
    assert is_bit_set(value, index) == expected


@pytest.mark.parametrize("invalid_value", [-1, 3.14])
def test_is_bit_set_invalid_value(invalid_value):
    with pytest.raises(ValueError) as e:
        is_bit_set(invalid_value, 0)
    msg = e.value.args[0]
    assert msg.startswith("Invalid parameter '{}'.".format(invalid_value))


@pytest.mark.parametrize(
    "byte_array, expected",
    [
        ([0x00, 0x0A, 0x5C], 2652),
        ([0xFF, 0xFC, 0x02], 16776194),
        ([0x01, 0x8A, 0x9E], 101022),
    ],
)
def test_array_block_to_unsigned_int(byte_array, expected):
    assert array_block_to_unsigned_int(byte_array) == expected


@pytest.mark.parametrize(
    "byte_array, index",
    [([-0x01, 0x00, 0xFF], 0), ([0x00, 1.234, 0xFF], 1), ([0x00, 0xFF, 0x100], 2)],
)
def test_array_block_to_unsigned_int_1_bad_value(byte_array, index):
    with pytest.raises(ValueError) as e:
        array_block_to_unsigned_int(byte_array)
    msg = e.value.args[0]
    assert msg.startswith("Value '{}' at index '{}'".format(byte_array[index], index))


def test_array_block_to_unsigned_int_multiple_bad_values():
    bad_byte_array = [-0x01, 1.234, 0x100]
    with pytest.raises(ValueError) as e:
        array_block_to_unsigned_int(bad_byte_array)
    msg = e.value.args[0]
    assert msg.startswith("Values [-1, 1.234, 256] at indeces [0, 1, 2]")


@pytest.mark.parametrize(
    "twos_compliment, bits, expected", [(16772216, 24, -5000), (5000, 24, 5000)]
)
def test_twos_compliment_to_signed_int(twos_compliment, bits, expected):
    value = twos_compliment_to_signed_int(twos_compliment, bits)
    assert value == expected


@pytest.mark.parametrize(
    "byte_array, expected",
    [
        ([0x00, 0x0A, 0x5C], 2652),
        ([0xFF, 0xFC, 0x02], -1022),
        ([0x01, 0x8A, 0x9E], 101022),
    ],
)
def test_array_block_to_signed_int(byte_array, expected):
    assert array_block_to_signed_int(byte_array) == expected
