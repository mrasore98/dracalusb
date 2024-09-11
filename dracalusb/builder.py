import logging
import shlex
import subprocess
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path


def builder_method(func):
    """
    Decorator to enable restoring previous commands and method chaining with DracalCmdBuilder.
    """
    def wrapper(builder, *args, **kwargs):
        # Update the previous command before editing command in func
        builder.previous_cmd = builder.cmd
        # Builder methods return no values
        func(builder, *args, **kwargs)
        # Return modified instance of builder to enable method chaining
        return builder

    return wrapper


class DracalTempUnits(StrEnum):
    """Valid temperature units for use with `dracal-usb-get`."""
    C = "C"
    F = "F"
    K = "K"
    CELSIUS = "Celsius"
    FAHRENHEIT = "Fahrenheit"
    KELVIN = "Kelvin"


class DracalPressureUnits(StrEnum):
    """Valid pressure units for use with `dracal-usb-get`."""
    K_PA = "kPa"
    H_PA = "hPa"
    PA = "Pa"
    BAR = "bar"
    AT = "at"  # 98.0665 kPa
    ATM = "atm"  # 101.325 kPa
    TORR = "Torr"
    PSI = "psi"
    IN_HG = "inHg"


class DracalFrequencyUnits(StrEnum):
    """Valid Frequency units for use with `dracal-usb-get`."""
    MILLI_HZ = "mHz"
    HZ = "Hz"
    K_HZ = "kHz"
    MEGA_HZ = "MHz"
    RPM = "rpm"


class DracalLengthUnits(StrEnum):
    """Valid length units for use with `dracal-usb-get`."""
    MILLI_METER = "mm"
    CENTI_METER = "cm"
    DECI_METER = "dm"
    METER = "m"
    MILE = "mil"
    INCH = "in"
    FEET = "ft"
    YARD = "yd"


class DracalConcentrationUnits(StrEnum):
    """Valid concentration units for use with `dracal-usb-get`."""
    PPB = "ppb"  # parts per billion
    PPM = "ppm"  # parts per million
    PERCENT = "percent"

class DracalUnits:
    temperature = DracalTempUnits
    pressure = DracalPressureUnits
    length = DracalLengthUnits
    frequency = DracalFrequencyUnits
    concentration = DracalConcentrationUnits

class DracalOptions(StrEnum):
    NO_HUMIDEX_RANGE = "no_humidex_range"  # Calculate humidex even if input values are out of range.
    NO_HEAT_INDEX_RANGE = "no_heat_index_range"  # Calculate heat index even if input values are out of range.
    LEGACY_ERRORS = "legacy_errors"  # Output channels errors in old (unspecific) way. For instance: "err" instead of "ProbeDisconnected"


class DracalCmdBuilder:
    """
    Constructs commands to execute with `dracal-usb-get`.

    Based on documentation from https://www.dracal.com/en/dracal-usb-get_howto/ for v3.2.1 updated 04-05-2023.
    """
    _base_command = "dracal-usb-get"
    units = DracalUnits
    options = DracalOptions


    def __init__(self, serial_number: str = None):
        self.cmd = self._base_command
        self.previous_cmd = self._base_command
        self.serial_number = serial_number
        self.logger = logging.getLogger(__name__)

    def __repr__(self):
        return f"{self.__class__.__name__}(serial_number:{self.serial_number}, cmd: '{self.cmd}')"

    def __str__(self):
        return self.cmd

    # *** DATA ACQUISITION ***
    @builder_method
    def use_sensor(self, serial_number: str) -> "DracalCmdBuilder":
        """
        Use USB sensor with matching serial number.

        Adds `-s` flag to command followed by specified serial number. If not provided, dracal-usb-get defaults to
        using the first found.

        :param serial_number: Serial number of Dracal sensor.
        """
        self.cmd += f" -s {serial_number.strip()}"

    @builder_method
    def use_first_sensor(self) -> "DracalCmdBuilder":
        """
        Use the "first sensor encountered".

        Best used when only one sensor is present.

        Note that the notion of "first sensor encountered" has nothing to do with the order of appearance of sensors
        when using `dracal-usb-get -l`.
        """
        self.cmd += " -f"

    def _check_use_channels_pre_argument(self, use_first_sensor: bool = True) -> bool:
        # Ensure sensor is specified
        if not (" -s " in self.cmd or " -f" in self.cmd):
            self.logger.debug("No sensor specified!")
            if self.serial_number is None:
                if use_first_sensor:
                    self.logger.debug("Using first sensor encountered.")
                    self.cmd += " -f"
                else:
                    self.logger.error("Must specify sensor to select channels. Consider enabling "
                                      "`use_first_sensor` if only one sensor is connected or provide a serial number.")
                    return False
            else:
                self.logger.debug(f"Using serial number {self.serial_number} provided at instantiation.")
                self.use_sensor(self.serial_number)
        return True

    @builder_method
    def use_channels(self, channels: Sequence[int] = None, use_first_sensor: bool = True) -> "DracalCmdBuilder":
        """
        Use specific channel(s) id(s).

        Adds `-i` flag to command followed by comma-separated list of channels. If not provided, dracal_usb-get
        defaults to 0.

        Must be used with `-s` flag (see `use_serial_number` method) or `-f` flag (see `use_first_sensor` method) to
        succeed.

        NOTE: To use all channels, see the `use_all_channels` method instead.

        :param channels: List of channel numbers to use. List elements must be integers.
        :param use_first_sensor: If no sensor has been previously specified, adds `-f` flag to use the first sensor
            encountered. If false and no sensor has been specified, this method will not modify the command.
        """
        # Ensure sensor is specified
        if not self._check_use_channels_pre_argument(use_first_sensor):
            self._restore_previous()  # Called mostly for logging, should have no impact on cmd here
            return

        # Validate integers
        if not all(isinstance(channel, int) for channel in channels):
            self.logger.error(f"A non-integer value was passed into the channel list: {channels}")
            # Revert changes if any
            self._restore_previous()
            return

        # Specify channels in command
        self.cmd += (" -i " + ",".join(str(channel) for channel in channels))

    @builder_method
    def use_all_channels(self, use_first_sensor: bool = True) -> "DracalCmdBuilder":
        """
        Use all available channels for a given sensor.

        Adds `-i` flag followed by `a` to indicate all channels should be used.

        Must be used with `-s` flag (see `use_serial_number` method) or `-f` flag (see `use_first_sensor` method) to
        succeed.

        NOTE: To specify a subset of channels, see the `use_channels` method instead.

        :param use_first_sensor: If no sensor has been previously specified, adds `-f` flag to use the first sensor
            encountered. If false and no sensor has been specified, this method will not modify the command.
        """
        # Ensure sensor is specified
        if not self._check_use_channels_pre_argument(use_first_sensor):
            self._restore_previous()  # Called mostly for logging, should have no impact on cmd here
            return

        self.cmd += " -i a"

    @builder_method
    def retries(self, num_retries: int) -> "DracalCmdBuilder":
        """
        If a USB command fails, retry it some number of times before bailing out.

        Adds `-R` flag to command followed by number of retries.

        :param num_retries: Number of times to retry command
        """
        # TODO: validate number of retries
        self.cmd += f" -R {num_retries}"

    # *** FORMATTING ***
    @builder_method
    def num_decimals(self, num: int) -> "DracalCmdBuilder":
        """
        Set number of fractional digits displayed in output.

        Valid range of [0 - 6]. If this method is not called, the `dracal-usb-get` default is 2.

        Adds `-x` flag to command followed by the number of decimals.

        :param num: Number of decimal points to display.
        """
        valid_range_min = 0
        valid_range_max = 6
        if num < valid_range_min or num > valid_range_max:
            self.logger.debug(f"Invalid number of decimal points provided: {num}.")
            self.logger.debug("Valid range: [0 - 6]")
            self._restore_previous()
            return

        self.cmd += f" -x {num}"

    @builder_method
    def ascii_output(self) -> "DracalCmdBuilder":
        """
        Use 7-bit ASCII output (no Unicode degree symbols).

        Adds `-7` flag to command.
        """
        self.cmd += " -7"

    @builder_method
    def pretty_output(self) -> "DracalCmdBuilder":
        """
        Enable pretty output.

        Adds `-p` flag to command.
        """
        self.cmd += " -p"

    # *** LOGGING ***

    _DEFAULT_NUM_MEASUREMENTS = 10

    @builder_method
    def log_to_file(self, file: str | Path, *, num_measurements: int = _DEFAULT_NUM_MEASUREMENTS,
                    recording_frequency_ms: int = None) -> "DracalCmdBuilder":
        """
        Log recorded data to a file in .csv format.

        Adds `-L <file> -r <num_measurements> [-I <recording_frequency>]` to the command, where square brackets
        indicate an optional addition.

        Data will still be shown in stdout while the file is being written.

        :param file: The path to the file where data will be stored. If file already exists, data will be appended.
        :param num_measurements: The number of measurements to take with the sensor.
            Can be set to 0 to run continuously (not recommended!). Default: 10
        :param recording_frequency_ms: Number of milliseconds between consecutive recordings.
        """
        if num_measurements < 0:
            self.logger.debug(f"Negative number input for number of measurements. "
                              f"Setting to {self._DEFAULT_NUM_MEASUREMENTS}")
            num_measurements = self._DEFAULT_NUM_MEASUREMENTS

        logging_cmd = f" -L {file!s} -r {num_measurements}"
        if recording_frequency_ms:
            logging_cmd += f" -I {recording_frequency_ms}"
        self.cmd += logging_cmd

    # Does not need command builder decorator since this calls log_to_file
    def log_for_duration(self, file: str | Path, duration_sec: float, *, num_measurements: int = _DEFAULT_NUM_MEASUREMENTS,
                         recording_frequency_ms: int = None):
        """
        Log data recorded for a given duration to a file in .csv format.

        Adds `-L <file> -r <calc_num_measurements> -I <calc_recording_frequency>` to the command, where `calc_*`
        parameters may be calculated values based on the duration provided. If `recording_frequency_ms` is provided,
        the number of measurements will be calculated and the user-entered recording frequency will be used. Otherwise,
        the frequency is the calculated value.

        Data will still be shown in stdout while the file is being written.

        :param file: The path to the file where data will be stored. If file already exists, data will be appended.
        :param duration_sec: Duration for logging in seconds.
        :param num_measurements: The number of measurements to take with the sensor.
            Can be set to 0 to run continuously (not recommended). Default: 10
        :param recording_frequency_ms: Number of milliseconds between consecutive recordings.
        """
        duration_ms = duration_sec * 1e3

        if num_measurements <= 0:
            self.logger.debug(f"Number of measurements must be greater than 0. "
                              f"Setting to {self._DEFAULT_NUM_MEASUREMENTS}")
            num_measurements = self._DEFAULT_NUM_MEASUREMENTS

        if recording_frequency_ms is not None:
            num_measurements = int(duration_ms // recording_frequency_ms)
        else:
            recording_frequency_ms = int(duration_ms // num_measurements)

        return self.log_to_file(file, num_measurements=num_measurements, recording_frequency_ms=recording_frequency_ms)

    # *** UNITS ***
    @builder_method
    def temperature_units(self, units: DracalTempUnits) -> "DracalCmdBuilder":
        """
        Select the temperature unit to use.

        Adds `-T <units>` to the command.

        :param units: The temperature unit to use.
        """
        self.cmd += f" -T {units!s}"

    @builder_method
    def pressure_units(self, units: DracalPressureUnits) -> "DracalCmdBuilder":
        """
        Select the pressure unit to use.

        Adds `-P <units>` to the command.

        :param units: The pressure unit to use.
        """
        self.cmd += f" -P {units!s}"

    @builder_method
    def frequency_units(self, units: DracalFrequencyUnits) -> "DracalCmdBuilder":
        """
        Select the frequency unit to use.

        Adds `-F <units>` to the command.

        :param units: The frequency unit to use.
        """
        self.cmd += f" -F {units!s}"

    @builder_method
    def length_units(self, units: DracalLengthUnits) -> "DracalCmdBuilder":
        """
        Select the length unit to use.

        Adds `-M <units>` to the command.

        :param units: The length unit to use.
        """
        self.cmd += f" -M {units!s}"

    @builder_method
    def concentration_units(self, units: DracalConcentrationUnits) -> "DracalCmdBuilder":
        """
        Select the concentration unit to use.

        Adds `-C <units>` to the command.

        :param units: The concentration unit to use.
        """
        self.cmd += f" -C {units!s}"

    @builder_method
    def enable_option(self, option: DracalOptions) -> "DracalCmdBuilder":
        """
        Enable specified option.

        Adds `-o <option>` to the command. You may use `-o` multiple times.

        :param option: The option to enable.
        """
        self.cmd += f" -o {option!s}"

    # *** BUILDER META ***
    @builder_method
    def reset(self) -> "DracalCmdBuilder":
        """Reset the command to prepare for a new command."""
        self.cmd = self._base_command
        self.logger.debug("Command was reset")

    def execute(self) -> str:
        """Run the built command and return the output."""
        output = None
        args = shlex.split(self.cmd)
        try:
            self.logger.debug("Executing command: " + self.cmd)
            output = subprocess.check_output(args)
            self.reset()
        except subprocess.CalledProcessError as e:
            self.logger.exception(e)
            raise
        return output.decode("utf-8").strip()

    def _restore_previous(self):
        self.logger.debug("No changes made to command string.")
        self.cmd = self.previous_cmd
        self.logger.debug(f"Current command string: {self.cmd}")
