import functools
import itertools

import smbus


BITS_IN_BYTE = 8


class BaseI2CDriver(object):
    """Base class for writing drivers for I2C sensors."""

    def __init__(self, address, port):
        self.bus = smbus.SMBus(port)
        self.address = address

    def read_byte_data(self, command):
        """
        :param int command: Byte to write to I2C device.
        :return int: Unsigned byte response from :attr:`command`.
        """
        BaseI2CDriver._check_is_unsigned_byte(command)
        return self.bus.read_byte_data(self.address, command)

    def read_block_data(self, command, length):
        """
        :param int command: Byte to write to I2C device.
        :param length: Number of bytes to read from I2C device.
        :return list: :attr:`length` byte sized int elements from I2C device.
        """
        BaseI2CDriver._check_is_unsigned_byte(command)
        return self.bus.read_i2c_block_data(self.address, command, length)

    def write_byte(self, command):
        """
        :param int command: Byte to write to I2C device.
        """
        BaseI2CDriver._check_is_unsigned_byte(command)
        self.bus.write_byte(self.address, command)

    @staticmethod
    def do_bitwise_or(val1, val2, *args):
        """
        :param int val1: First number.
        :param int val2: Second number.
        :param int args: Optional subsequent numbers.
        :return int: Value from using bitwise or operator on all args.
        """
        values = itertools.chain([val1, val2], args)
        return functools.reduce(lambda x, y: x | y, values)

    @staticmethod
    def is_unsigned_byte(byte):
        """
        :param int byte: Value to test.
        :return bool: True if :attr:`byte` contains 8 bits and is non-negative.
        """
        return isinstance(byte, int) and 0x00 <= byte <= 0xff

    @staticmethod
    def _check_is_unsigned_byte(value):
        if not BaseI2CDriver.is_unsigned_byte(value):
            msg = "'{}' is not an unsigned byte.".format(value)
            raise ValueError(msg)

    @staticmethod
    def is_bit_set(value, index):
        """
        :param int value: Positive integer to test.
        :param int index: 0-based index of bit in :attr:`value` to check.
        :return bool: True if bit in :attr:`value` at :attr:`index` is set.
        """
        if not isinstance(value, int) or value < 0:
            msg_template = "Invalid parameter '{}'. Use positive integer."
            raise ValueError(msg_template.format(value))
        mask = 1 << index
        bit = (value & mask) >> index
        return bit == 1

    @staticmethod
    def array_block_to_unsigned_int(data_array):
        """
        :param list data_array: List of byte values.
        :return int: Unsigned integer value of :attr:`data_array`.
        """
        are_bytes = [BaseI2CDriver.is_unsigned_byte(i) for i in data_array]
        if not all(are_bytes):
            BaseI2CDriver._raise_not_bytes_value_error(data_array, are_bytes)
        value = 0
        for byte in data_array:
            value <<= BITS_IN_BYTE
            value |= byte
        return value

    @staticmethod
    def _raise_not_bytes_value_error(data, are_bytes):
        not_bytes = [(datum, i)
                     for i, (datum, is_byte) in enumerate(zip(data, are_bytes))
                     if not is_byte]
        if len(not_bytes) == 1:
            msg_template = "Value '{}' at index '{}' is not an unsigned byte."
            msg = msg_template.format(not_bytes[0][0], not_bytes[0][1])
        else:
            msg_template = 'Values {} at indeces {} are not unsigned bytes.'
            msg = msg_template.format(repr([d for d, _ in not_bytes]),
                                      repr([i for _, i in not_bytes]))
        raise ValueError(msg)

    @staticmethod
    def array_block_to_int(data_array):
        """
        :param list data_array: List of byte values in 2's complement format.
        :return int: Signed integer value of :attr:`data_array`.
        """
        value = BaseI2CDriver.array_block_to_unsigned_int(data_array)
        bits = len(data_array) * BITS_IN_BYTE
        return BaseI2CDriver.twos_compliment_to_signed_int(value, bits)

    @staticmethod
    def twos_compliment_to_signed_int(twos_compliment_value, bits):
        """From http://stackoverflow.com/a/9147327.

        :param int twos_compliment_value: 2's compliment unsigned value
        :param int bits: Number of bits in :attr:`twos_compliment_value`
        :return int: Signed version of :attr:`twos_compliment_value`
        """
        if BaseI2CDriver.is_bit_set(twos_compliment_value, bits - 1):
            twos_compliment_value -= (1 << bits)
        return twos_compliment_value
