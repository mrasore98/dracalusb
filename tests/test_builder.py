import pytest

from dracalusb.builder import DracalCmdBuilder


@pytest.fixture
def cmd_builder() -> DracalCmdBuilder:
    builder = DracalCmdBuilder
    yield builder
    builder.reset()


class TestDracalCmdBuilder:
    def test_use_sensor(self, cmd_builder):
        builder = cmd_builder
        builder.use_sensor("MY_SENSOR")
        assert builder.cmd == "dracal-get-usb -s MY_SENSOR"

    def test_use_first_sensor(self):
        pass

    def test_use_channels_with_previous_sensor(self):
        pass

    def test_use_channels_with_instance_sensor(self):
        pass

    def test_use_channels_no_sensor_use_first_true(self):
        pass

    def test_use_channels_no_sensor_use_first_false(self):
        pass

    def test_use_channels_integer_validation(self):
        pass

    def test_use_all_channels(self):
        pass

    def test_num_decimals_valid(self):
        pass

    def test_num_decimals_invalid(self):
        pass

    def test_retries(self):
        pass

    def test_ascii_output(self):
        pass

    def test_log_to_file_defaults(self):
        pass

    def test_log_to_file_num_meas(self):
        pass

    def test_log_to_file_recording_freq(self):
        pass

    def test_log_to_file_duration(self):
        pass

    def test_reset(self):
        pass

