import pytest
import six
import smbus

from barometerdrivers import HP206C

if six.PY2:
    import mock
else:
    import unittest.mock as mock


address = 0x76


@pytest.fixture(scope='module')
def hp206c(request):
    # mock smbus calls used in HP206C constructor
    open_patcher = mock.patch.object(smbus.SMBus, 'open')
    write_patcher = mock.patch.object(smbus.SMBus, 'write_byte')
    read_patcher = mock.patch.object(smbus.SMBus, 'read_byte_data',
                                     side_effect=[0x40])
    # get smbus mock objects
    open_mock = open_patcher.start()
    write_mock = write_patcher.start()
    read_mock = read_patcher.start()

    def teardown():
        open_patcher.stop()
        write_patcher.stop()
        read_patcher.stop()

    # instantiate barometer driver
    barometer = HP206C()

    # assert smbus is being called correctly
    open_mock.assert_called_once_with(1)
    write_mock.assert_called_once_with(address, 0x06)
    read_mock.assert_called_once_with(address, 0x80 | 0x0d)

    request.addfinalizer(teardown)
    return barometer


def test_set_oversampling_rate_error(hp206c):
    with pytest.raises(ValueError) as e:
        hp206c.oversampling_rate = 555
    msg = e.value.args[0]
    assert msg.startswith("'555'")
    assert msg.endswith('Choose 128, 256, 512, 1024, 2048, 4096.')


@mock.patch.object(smbus.SMBus, 'write_byte')
@mock.patch.object(smbus.SMBus, 'read_byte_data', side_effect=[0x40])
@mock.patch.object(smbus.SMBus, 'read_i2c_block_data',
                   side_effect=[[0x00, 0x0a, 0x5c]])
def test_read_temperature_26C(read_i2c_mock, read_mock, write_mock, hp206c):
    assert hp206c.read_temperature() == 26.52
    write_mock.assert_called_once_with(address, 0x40 | 0x02)
    read_mock.assert_called_once_with(address, 0x80 | 0x0d)
    read_i2c_mock.assert_called_once_with(address, 0x32, 3)


@mock.patch.object(smbus.SMBus, 'write_byte')
@mock.patch.object(smbus.SMBus, 'read_byte_data', side_effect=[0x00, 0x40])
@mock.patch.object(smbus.SMBus, 'read_i2c_block_data',
                   side_effect=[[0xff, 0xfc, 0x02]])
def test_read_temperature_n10C(read_i2c_mock, read_mock, write_mock, hp206c):
    assert hp206c.read_temperature() == -10.22
    write_mock.assert_called_once_with(address, 0x40 | 0x02)
    assert read_mock.call_args_list == [mock.call(address, 0x80 | 0x0d)] * 2
    read_i2c_mock.assert_called_once_with(address, 0x32, 3)


@mock.patch.object(smbus.SMBus, 'write_byte')
@mock.patch.object(smbus.SMBus, 'read_byte_data', side_effect=[0x40])
@mock.patch.object(smbus.SMBus, 'read_i2c_block_data',
                   side_effect=[[0x01, 0x8a, 0x9e]])
def test_read_pressure_1010mbar(read_i2c_mock, read_mock, write_mock, hp206c):
    assert hp206c.read_pressure() == 1010.22
    write_mock.assert_called_once_with(address, 0x40)
    read_mock.assert_called_once_with(address, 0x80 | 0x0d)
    read_i2c_mock.assert_called_once_with(address, 0x30, 3)


@mock.patch.object(smbus.SMBus, 'write_byte')
@mock.patch.object(smbus.SMBus, 'read_byte_data', side_effect=[0x40])
@mock.patch.object(smbus.SMBus, 'read_i2c_block_data',
                   side_effect=[[0x00, 0x0a, 0x5c, 0x01, 0x8a, 0x9e]])
def test_read_temperature_and_pressure_26C_1010mbar(
        read_i2c_mock, read_mock, write_mock, hp206c):
    assert hp206c.read_temperature_and_pressure() == (26.52, 1010.22)
    write_mock.assert_called_once_with(address, 0x40)
    read_mock.assert_called_once_with(address, 0x80 | 0x0d)
    read_i2c_mock.assert_called_once_with(address, 0x10, 6)
