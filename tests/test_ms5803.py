import pytest

from barometerdrivers import MS5803_01BA
from barometerdrivers.basei2c import BaseI2CDriver as I2C
from barometerdrivers.ms5803 import Reading

try:
    from unittest.mock import patch, call
except ImportError:
    from mock import patch, call


def test_invalid_address():
    with pytest.raises(ValueError) as e:
        MS5803_01BA(0x01)
    msg = e.value.args[0]
    assert msg == "Invalid address '0x1'. Valid addresses are 0x76 or 0x77."


@patch.object(I2C, '__init__')
@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_block_data', side_effect=lambda a, l: list(range(l)))
def mock_ms5803(ms5803_class, read_mock, write_mock, init_mock):
    barometer = ms5803_class(0x77, port=0)

    init_mock.assert_called_once_with(0x77, 0)
    write_mock.assert_called_once_with(MS5803_01BA.reset)
    prom_cmds = [0xa2 + i for i in range(0, 12, 2)]
    read_calls = [call(cmd, 2) for cmd in prom_cmds]
    read_mock.assert_has_calls(read_calls, any_order=True)
    assert len(read_mock.call_args_list) == len(read_calls)

    return barometer


@pytest.fixture(scope='module')
def ms5803_01ba():
    barometer = mock_ms5803(MS5803_01BA)

    # populate coefficients with values from real sensor
    barometer.sens_t1 = 42345
    barometer.off_t1 = 39999
    barometer.tcs = 24942
    barometer.tco = 25426
    barometer.t_ref = 33098
    barometer.tempsens = 28278
    return barometer


def test_set_oversampling_rate_error(ms5803_01ba):
    with pytest.raises(ValueError) as e:
        ms5803_01ba.oversampling_rate = 555
    msg = e.value.args[0]
    assert msg.startswith("'555'")
    assert msg.endswith('Choose 256, 512, 1024, 2048, 4096.')


@pytest.mark.parametrize('osr, expected_command', [
    (256, {'pressure': 0x40, 'temperature': 0x50}),
    (512, {'pressure': 0x42, 'temperature': 0x52}),
    (1024, {'pressure': 0x44, 'temperature': 0x54}),
    (2048, {'pressure': 0x46, 'temperature': 0x56}),
    (4096, {'pressure': 0x48, 'temperature': 0x58})
])
def test_set_oversampling_rate(ms5803_01ba, osr, expected_command):
    ms5803_01ba.oversampling_rate = osr
    osr_command = ms5803_01ba.osr_conversion[osr]['command']
    assert osr_command(Reading.PRESSURE) == expected_command['pressure']
    assert osr_command(Reading.TEMPERATURE) == expected_command['temperature']


@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_block_data', side_effect=[[0x81, 0x4b, 0x0c]])
def test_read_temperature_20C(read_mock, write_mock, ms5803_01ba):
    assert ms5803_01ba.read_temperature() == 20.0
    write_mock.assert_called_once_with(0x58)
    read_mock.assert_called_once_with(0x00, 3)


@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_block_data', side_effect=[[0x81, 0x4b, 0x0c],
                                                   [0x88, 0x05, 0xd2]])
def test_read_temp_pressure_20C_1000mbar(read_mock, write_mock, ms5803_01ba):
    assert ms5803_01ba.read_temperature_and_pressure() == (20.0, 1000.0)
    assert write_mock.call_args_list == [call(i) for i in [0x58, 0x48]]
    assert read_mock.call_args_list == [call(0x00, 3)] * 2


@patch.object(I2C, 'write_byte')
@patch.object(I2C, 'read_block_data', side_effect=[[0x81, 0x4b, 0x0c],
                                                   [0x88, 0x05, 0xd2]])
def test_read_pressure_1000mbar(read_mock, write_mock, ms5803_01ba):
    assert ms5803_01ba.read_pressure() == 1000.0
    assert write_mock.call_args_list == [call(i) for i in [0x58, 0x48]]
    assert read_mock.call_args_list == [call(0x00, 3)] * 2


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
