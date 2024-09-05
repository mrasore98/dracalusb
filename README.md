# `dracalusb`

Python wrapper for Dracal Technologies' `dracal-usb-get` command line tool. 

** This library is not yet feature complete

## Prerequisites

1. [DracalView](https://www.dracal.com/en/software/) is installed.
2. `dracal-usb-get` is in your PATH.

## Usage

This library is sensor agnostic, so should be usable with any Dracal sensor that is compatible with Dracal's 
`dracal-usb-get` CLI tool.

### Direct Usage

To create and execute a command using this library, first create an instance of `DracalCmdBuilder` and use its methods
to compose your command. 

```python
from dracalusb.builder import DracalCmdBuilder

bldr = DracalCmdBuilder()

# Use commands one by one...
bldr.use_sensor("E123456")  # cmd = "dracal-get-usb -s E123456"
bldr.use_all_channels()  # cmd = "dracal-get-usb -s E123456 -i a"
# ... or use method chains
bldr.num_decimals(4).pretty_output().ascii_output()  # cmd = "dracal-get-usb -s E123456 -i a -x 4 -p -7"

# Call `execute` to run the composed command 
result = bldr.execute()
```

### Building Sensors

This library was intended to be an intermediate library that could be used to build different sensor classes while
providing the flexibility to create other commands on the fly. For example,

```python
from dracalusb.builder import DracalCmdBuilder, DracalUnits

class TRH420:
    """Controller class for Dracal USB-TRH420"""
    def __init__(self, serial_num: str = None):
        self.builder = DracalCmdBuilder(serial_num)
    
    def measure_temp_fahrenheit(self) -> float:
        self.builder.use_channels([0]).temperature_units(DracalUnits.temperature.F)
        temp_f_str = self.builder.execute()
        return float(temp_f_str)
```

## Resources

* [dracal-usb-get Documentation](https://www.dracal.com/en/dracal-usb-get_howto/)
* [DracalView download](https://www.dracal.com/en/software/)