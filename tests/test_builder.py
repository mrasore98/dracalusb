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

    @pytest.mark.skip(reason="Not implemented yet")
    def test_log_to_file_duration(self, cmd_builder):
        pass

    def test_reset(self, cmd_builder):
        cmd_builder.cmd = "NONSENSE STRING"
        cmd_builder.reset()
        assert cmd_builder.cmd == "dracal-usb-get"

    @pytest.mark.skip(reason="Not implemented yet")
    def test_execute(self, cmd_builder):
        pass

