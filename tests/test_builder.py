import shlex
from unittest.mock import patch

import pytest

from dracalusb.builder import DracalCmdBuilder


@pytest.fixture
def cmd_builder() -> DracalCmdBuilder:
    builder = DracalCmdBuilder()
    yield builder
    builder.reset()


class TestDracalCmdBuilder:
    def test_builder_method(self, cmd_builder):
        arbitrary_cmd = "SOME COMMAND"
        cmd_builder.cmd = arbitrary_cmd
        # Check return type of a method decorated by `builder_method`
        assert type(cmd_builder.reset()) is DracalCmdBuilder
        assert cmd_builder.previous_cmd == arbitrary_cmd

    def test_use_sensor(self, cmd_builder):
        cmd_builder.use_sensor("MY_SENSOR")
        assert cmd_builder.cmd == "dracal-usb-get -s MY_SENSOR"

    def test_use_first_sensor(self, cmd_builder):
        cmd_builder.use_first_sensor()
        assert cmd_builder.cmd == "dracal-usb-get -f"

    def test_use_channels_with_previous_sensor(self, cmd_builder):
        cmd_builder.use_sensor("MY_SENSOR").use_channels([0, 1, 2, 3])
        assert cmd_builder.cmd == "dracal-usb-get -s MY_SENSOR -i 0,1,2,3"

    def test_use_channels_with_instance_sensor(self, cmd_builder):
        cmd_builder.serial_number = "INSTANCE_SN"
        cmd_builder.use_channels([0, 1])
        assert cmd_builder.cmd == "dracal-usb-get -s INSTANCE_SN -i 0,1"

    def test_use_channels_no_sensor_use_first_true(self, cmd_builder):
        cmd_builder.use_channels([0, 1])
        assert cmd_builder.cmd == "dracal-usb-get -f -i 0,1"

    def test_use_channels_no_sensor_use_first_false(self, cmd_builder):
        expected_cmd = cmd_builder.cmd
        cmd_builder.use_channels([0, 1], use_first_sensor=False)
        assert cmd_builder.cmd == expected_cmd


    def test_use_channels_integer_validation(self, cmd_builder):
        expected_cmd = cmd_builder.cmd
        cmd_builder.use_channels([0, 1, "2"])
        assert cmd_builder.cmd == expected_cmd

    def test_use_all_channels(self, cmd_builder):
        cmd_builder.use_all_channels()
        assert cmd_builder.cmd == "dracal-usb-get -f -i a"

    def test_num_decimals_valid(self, cmd_builder):
        cmd_builder.num_decimals(3)
        assert cmd_builder.cmd == "dracal-usb-get -x 3"

    def test_num_decimals_invalid(self, cmd_builder):
        expected_cmd = cmd_builder.cmd
        cmd_builder.num_decimals(-1)
        assert expected_cmd == cmd_builder.cmd
        cmd_builder.num_decimals(7)
        assert expected_cmd == cmd_builder.cmd

    def test_retries(self, cmd_builder):
        cmd_builder.retries(4)
        assert cmd_builder.cmd == "dracal-usb-get -R 4"

    def test_ascii_output(self, cmd_builder):
        cmd_builder.ascii_output()
        assert cmd_builder.cmd == "dracal-usb-get -7"

    def test_pretty_output(self, cmd_builder):
        cmd_builder.pretty_output()
        assert cmd_builder.cmd == "dracal-usb-get -p"

    def test_log_to_file_defaults(self, cmd_builder):
        cmd_builder.log_to_file("my_log.txt")
        assert cmd_builder.cmd == "dracal-usb-get -L my_log.txt -r 10"

    def test_log_to_file_num_meas(self, cmd_builder):
        cmd_builder.log_to_file("my_log.txt", num_measurements=3)
        assert cmd_builder.cmd == "dracal-usb-get -L my_log.txt -r 3"

    def test_log_to_file_recording_freq(self, cmd_builder):
        cmd_builder.log_to_file("my_log.txt", recording_frequency_ms=100)
        assert cmd_builder.cmd == "dracal-usb-get -L my_log.txt -r 10 -I 100"

    def test_log_to_file_duration(self, cmd_builder):
        cmd_builder.log_for_duration("-", 30, num_measurements=15)
        assert cmd_builder.cmd == "dracal-usb-get -L - -r 15 -I 2000"
        cmd_builder.reset()
        cmd_builder.log_for_duration("file.csv", 20, recording_frequency_ms=4000)
        assert cmd_builder.cmd == "dracal-usb-get -L file.csv -r 5 -I 4000"

    def test_units(self, cmd_builder):
        cmd_builder.temperature_units(DracalCmdBuilder.units.temperature.F)
        cmd_builder.pressure_units(DracalCmdBuilder.units.pressure.ATM)
        cmd_builder.length_units(DracalCmdBuilder.units.length.CENTI_METER)
        cmd_builder.frequency_units(DracalCmdBuilder.units.frequency.RPM)
        cmd_builder.concentration_units(DracalCmdBuilder.units.concentration.PPB)
        assert cmd_builder.cmd == "dracal-usb-get -T F -P atm -M cm -F rpm -C ppb"

    def test_enable_option(self, cmd_builder):
        cmd_builder.enable_option(DracalCmdBuilder.options.LEGACY_ERRORS)
        cmd_builder.enable_option(DracalCmdBuilder.options.NO_HUMIDEX_RANGE)
        cmd_builder.enable_option(DracalCmdBuilder.options.NO_HEAT_INDEX_RANGE)
        assert cmd_builder.cmd == "dracal-usb-get -o legacy_errors -o no_humidex_range -o no_heat_index_range"

    def test_reset(self, cmd_builder):
        cmd_builder.cmd = "NONSENSE STRING"
        cmd_builder.reset()
        assert cmd_builder.cmd == "dracal-usb-get"

    def test_execute(self, cmd_builder):
        cmd_builder.cmd = "dracal-usb-get -f -i 0,1 -x 2"
        expected_args = shlex.split(cmd_builder.cmd)
        with patch("subprocess.check_output") as mock_check_output:
            mock_check_output.return_value = "25.04, 40.02\r\n".encode()

            result = cmd_builder.execute()

            mock_check_output.assert_called_with(expected_args)
            assert result == "25.04, 40.02"
            assert cmd_builder.cmd == "dracal-usb-get"

