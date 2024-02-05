from unittest.mock import call

import pytest

from barometerdrivers import MS5803_01BA


def read_prom_side_effect(cmd, _):
    """Returns example values from datasheet."""
    cmd_to_bytes = {
        0xA2: [0x9C, 0xBF],  # sens_t1 = 40127
        0xA4: [0x90, 0x3C],  # off_t1 = 36924
        0xA6: [0x5B, 0x15],  # tcs = 23317
        0xA8: [0x5A, 0xF2],  # tco = 23282
        0xAA: [0x82, 0xB8],  # t_ref = 33464
        0xAC: [0x6E, 0x98],  # tempsens = 28312
    }
    return cmd_to_bytes[cmd]


def test_ms5803_0b1a_init(i2c_mock_init, i2c_mock):
    i2c_mock.read_block_data.side_effect = read_prom_side_effect
    barometer = MS5803_01BA()

    i2c_mock_init.assert_called_once_with(0x77, 1)
    i2c_mock.write_byte.assert_called_once_with(MS5803_01BA.reset)
    prom_cmds = [0xA2 + i for i in range(0, 12, 2)]
    read_calls = [call(cmd, 2) for cmd in prom_cmds]
    i2c_mock.read_block_data.assert_has_calls(read_calls, any_order=True)
    assert len(i2c_mock.read_block_data.mock_calls) == len(read_calls)
    assert barometer.sens_t1 == 40127
    assert barometer.off_t1 == 36924
    assert barometer.tcs == 23317
    assert barometer.tco == 23282
    assert barometer.t_ref == 33464
    assert barometer.tempsens == 28312


@pytest.fixture
def ms5803_01ba(i2c_mock):
    i2c_mock.read_block_data.side_effect = read_prom_side_effect
    barometer = MS5803_01BA()
    i2c_mock.write_byte.reset_mock()
    i2c_mock.read_block_data.reset_mock()
    return barometer


def test_set_oversampling_rate_error(ms5803_01ba):
    with pytest.raises(ValueError) as e:
        ms5803_01ba.oversampling_rate = 555
    msg = e.value.args[0]
    assert msg.startswith("'555'")
    assert msg.endswith("Choose 256, 512, 1024, 2048, 4096.")


@pytest.mark.parametrize(
    "osr, pressure_cmd, temp_cmd",
    [
        (256, 0x40, 0x50),
        (512, 0x42, 0x52),
        (1024, 0x44, 0x54),
        (2048, 0x46, 0x56),
        (4096, 0x48, 0x58),
    ],
)
def test_set_oversampling_rate(ms5803_01ba, osr, pressure_cmd, temp_cmd):
    ms5803_01ba.oversampling_rate = osr
    osr_command = ms5803_01ba.osr_conversion[osr].command
    assert osr_command(is_pressure=True) == pressure_cmd
    assert osr_command(is_pressure=False) == temp_cmd


@pytest.mark.parametrize(
    "temp_bytes, expected_temp",
    [
        ([0x82, 0xC1, 0x3E], 20.07),
        ([0x90, 0x48, 0xB8], 50.0),
        ([0x7A, 0x50, 0x80], 0.0),
        ([0x6F, 0x76, 0x60], -30.0),
    ],
)
def test_read_temperature(i2c_mock, ms5803_01ba, temp_bytes, expected_temp):
    i2c_mock.read_block_data.side_effect = [temp_bytes]

    assert ms5803_01ba.read_temperature() == expected_temp
    i2c_mock.write_byte.assert_called_once_with(
        MS5803_01BA.osr_conversion[1024].command(is_pressure=False)
    )
    i2c_mock.read_block_data.assert_called_once_with(MS5803_01BA.read_adc, 3)


def test_read_temp_pressure_20C_1000mbar(i2c_mock, ms5803_01ba):
    i2c_mock.read_block_data.side_effect = [[0x82, 0xC1, 0x3E], [0x8A, 0xA2, 0x1A]]

    assert ms5803_01ba.read_temperature_and_pressure() == (20.07, 1000.09)
    assert i2c_mock.write_byte.mock_calls == [
        call(i)
        for i in (
            MS5803_01BA.osr_conversion[1024].command(is_pressure=False),
            MS5803_01BA.osr_conversion[1024].command(is_pressure=True),
        )
    ]
    assert i2c_mock.read_block_data.mock_calls == [call(MS5803_01BA.read_adc, 3)] * 2


def test_read_pressure_1000mbar(i2c_mock, ms5803_01ba):
    i2c_mock.read_block_data.side_effect = [[0x82, 0xC1, 0x3E], [0x8A, 0xA2, 0x1A]]

    assert ms5803_01ba.read_pressure() == 1000.09
    assert i2c_mock.write_byte.mock_calls == [
        call(i)
        for i in (
            MS5803_01BA.osr_conversion[1024].command(is_pressure=False),
            MS5803_01BA.osr_conversion[1024].command(is_pressure=True),
        )
    ]
    assert i2c_mock.read_block_data.mock_calls == [call(MS5803_01BA.read_adc, 3)] * 2
