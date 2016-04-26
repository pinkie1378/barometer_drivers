import pytest
import six
import smbus

from barometerdrivers import MS5803_01BA

if six.PY2:
    import mock
else:
    import unittest.mock as mock


address = 0x77


@pytest.fixture(scope='module')
def ms5803_01ba(request):
    # mock smbus calls used in MS5803_01BA constructor
    open_patcher = mock.patch.object(smbus.SMBus, 'open')
    write_patcher = mock.patch.object(smbus.SMBus, 'write_byte')
    read_patcher = mock.patch.object(
        smbus.SMBus, 'read_i2c_block_data', side_effect=[
            [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6]
        ]
    )
    # get smbus mock objects
    open_mock = open_patcher.start()
    write_mock = write_patcher.start()
    read_mock = read_patcher.start()

    def teardown():
        open_patcher.stop()
        write_patcher.stop()
        read_patcher.stop()

    # instantiate barometer driver
    port = 0
    barometer = MS5803_01BA(address, port=port)

    # assert smbus is being called correctly
    open_mock.assert_called_once_with(port)
    write_mock.assert_called_once_with(address, MS5803_01BA.reset)
    assert read_mock.call_count == 6
    prom_cmds = [0xa2 + i for i in range(0, 12, 2)]
    for cmd in prom_cmds:
        read_mock.assert_any_call(address, cmd, 2)

    # populate coefficients with values from real sensor
    barometer.sens_t1 = 42345
    barometer.off_t1 = 39999
    barometer.tcs = 24942
    barometer.tco = 25426
    barometer.t_ref = 33098
    barometer.tempsens = 28278

    request.addfinalizer(teardown)
    return barometer


@mock.patch.object(smbus.SMBus, 'write_byte')
@mock.patch.object(
    smbus.SMBus, 'read_i2c_block_data', side_effect=[[0x81, 0x4b, 0x0c]])
def test_read_temperature_20C(read_mock, write_mock, ms5803_01ba):
    assert ms5803_01ba.read_temperature() == 20.0
    write_mock.assert_called_once_with(address, 0x58)
    read_mock.assert_called_once_with(address, 0x00, 3)


@mock.patch.object(smbus.SMBus, 'write_byte')
@mock.patch.object(
    smbus.SMBus, 'read_i2c_block_data',
    side_effect=[[0x81, 0x4b, 0x0c], [0x88, 0x05, 0xd2]])
def test_read_temperature_and_pressure_20C_1000mbar(
        read_mock, write_mock, ms5803_01ba):
    assert ms5803_01ba.read_temperature_and_pressure() == (20.0, 1000.0)
    assert write_mock.call_args_list == (
        [mock.call(address, i) for i in [0x58, 0x48]])
    assert read_mock.call_args_list == [mock.call(address, 0x00, 3)] * 2


@mock.patch.object(smbus.SMBus, 'write_byte')
@mock.patch.object(
    smbus.SMBus, 'read_i2c_block_data',
    side_effect=[[0x81, 0x4b, 0x0c], [0x88, 0x05, 0xd2]])
def test_read_pressure_1000mbar(read_mock, write_mock, ms5803_01ba):
    assert ms5803_01ba.read_pressure() == 1000.0
    assert write_mock.call_args_list == (
        [mock.call(address, i) for i in [0x58, 0x48]])
    assert read_mock.call_args_list == [mock.call(address, 0x00, 3)] * 2


@pytest.mark.parametrize('temp_int, d_t, expected', [
    (493, -446988, {'temp': 4.0, 'off2': 6813147, 'sens2': 1987167}),
    (-1883, -1151988, {'temp': -25.0, 'off2': 45233067, 'sens2': 13486355}),
    (5500, 1038412, {'temp': 55.0, 'off2': 0, 'sens2': -125000})
])
def test_second_order_temp_conversion(ms5803_01ba, temp_int, d_t, expected):
    ms5803_01ba.d_t = d_t
    temp = ms5803_01ba._second_order_temp_conversion(temp_int)
    assert temp == expected['temp']
    assert ms5803_01ba.off2 == expected['off2']
    assert ms5803_01ba.sens2 == expected['sens2']
