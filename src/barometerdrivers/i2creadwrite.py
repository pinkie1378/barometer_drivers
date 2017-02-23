import smbus

from .helpers.decorators import validate_unsigned_byte_command


class I2CReadWrite(object):
    """Communicate with sensors on I2C bus."""

    def __init__(self, address, port):
        self.bus = smbus.SMBus(port)
        self.address = address

    @validate_unsigned_byte_command
    def read_byte_data(self, command):
        """
        :param int command: Byte to write to I2C device.
        :return int: Unsigned byte response from :attr:`command`.
        """
        return self.bus.read_byte_data(self.address, command)

    @validate_unsigned_byte_command
    def read_block_data(self, command, length):
        """
        :param int command: Byte to write to I2C device.
        :param length: Number of bytes to read from I2C device.
        :return list: :attr:`length` byte sized int elements from I2C device.
        """
        return self.bus.read_i2c_block_data(self.address, command, length)

    @validate_unsigned_byte_command
    def write_byte(self, command):
        """
        :param int command: Byte to write to I2C device.
        """
        self.bus.write_byte(self.address, command)
