# Purpose

To create a python API for working with National Instruments NIDAQmx.  Check
the [documentation](https://daqmx.readthedocs.io/en/latest/index.html) for
details.

## Project Maturity

The project is somewhat immature, but works well for where items are
implemented.  Currently, it has been tested on a single model device; however
there is no reason to suspect that the project wouldn't work on any device
that supports digital IO, analog inputs, and analog outputs.  There is 
approximately ~80% test coverage and a pretty good start on the
[documentation](https://daqmx.readthedocs.io/en/latest/index.html).

## Installation

    python -m pip install daqmx

## Usage

You must first import the package:

    from daqmx import NIDAQmxInstrument
    
You can then allocate the hardware without any further specifiers.  Note that, 
if there is more than one DAQmx instrument available on your PC, the hardware
allocated may not be the one you are expecting!  Be sure to specify the device
name, model number, or serial number to make the hardware acquisition process
more deterministic.

    daq = NIDAQmxInstrument()  # hardware with no specifiers
    
    daq = NIDAQmxInstrument(device_name='Dev3')  # hardware specified by the device name
    
    daq = NIDAQmxInstrument(model_number='USB-6001')  # hardware specified by model number

    daq = NIDAQmxInstrument(serial_number=1234)  # hardware specified by serial number
    
Once you have the `NIDAQmxInstrument` instance, then you can use it to operate
the instrument.  See the [examples](./examples) directory for complete examples.  
Some snippets to demonstrate common usages:

    daq = NIDAQmxInstrument()  # automatic acquisition of hardware

    daq.ao0 = 2.7  # set the analog out 0 to 2.7V
    daq.ao1 = 1.3  # set the analog out 1 to 1.3V

    print(f'daq.ai0.value: {daq.ai0.value:.3f}V')  # print a single sample 
                                                   # from analog input 0

    values = daq.ai1.capture(
        sample_count=10, rate=100,
        max_voltage=10.0, min_voltage=-10.0,
        mode='differential', timeout=3.0
    )  # capture 10 samples from ai1 at a rate of 100Hz in differential mode
    print(values)

    daq.port0.line2 = True  # set the daq.<port>.<line> to True or False to write
    print(daq.port0.line3)  # read the daq.<port>.<line> to read state of line

## Contribution Guidelines

Since I don't have access to unlimited instruments, I have to trust that 
contributions that say they work do actually work.  As a result, any new 
instruments that are contributed should have the following:

 - An issue associated with the instrument
 - A test in the `test` directory which describes the necessary 
   connections and implements testing

Pull requests are welcome!