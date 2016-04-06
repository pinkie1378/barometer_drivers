from abc import ABCMeta


BITS_IN_BYTE = 8


class ABCI2CDriver(object):
    """Base class for writing drivers for I2C sensors."""
    __metaclass__ = ABCMeta

    @staticmethod
    def array_block_to_value(data_array):
        """
        :param list data_array: List of byte values comprising a sensor
         measurement in 2's complement format.
        :return int: Signed integer value of :attr:`data_array`.
        """
        assert not [i for i in data_array if i >= 2**BITS_IN_BYTE]
        bits = len(data_array) * BITS_IN_BYTE
        value = 0
        for byte in data_array:
            value <<= BITS_IN_BYTE
            value |= byte
        return ABCI2CDriver.twos_compliment_to_signed_int(value, bits)

    @staticmethod
    def twos_compliment_to_signed_int(twos_compliment_value, bits):
        """From http://stackoverflow.com/a/9147327

        :param int twos_compliment_value: 2's compliment unsigned value
        :param int bits: Number of bits in :attr:`twos_compliment_value`
        :return int: Signed version of :attr:`twos_compliment_value`
        """
        if (twos_compliment_value & (1 << (bits - 1))) != 0:
            twos_compliment_value -= (1 << bits)
        return twos_compliment_value
