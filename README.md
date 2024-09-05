# `dracalusb`

Python wrapper for Dracal Technologies' `dracal-usb-get` command line tool. 

## Prerequisites

1. [DracalView](https://www.dracal.com/en/software/) is installed.
2. `dracal-usb-get` is in your PATH.

## Usage

This library is sensor agnostic, so should be usable with any Dracal sensor that is compatible with Dracal's 
`dracal-usb-get` CLI tool.

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
