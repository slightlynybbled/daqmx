# Purpose

To create a python API for working with National Instruments NIDAQmx.

## Installation

 1. Download the wheel file
 1. On the command line, navigate to the repository
 1. Run `python -m pip install <path-to-wheel-file>`

## Usage

You must first import the package:

    from ni import NIDAQmxInstrument
    
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
the instrument.

Some available methods:

    # set port0/line2 to "high"
    daq.digital_out_line(port_name='port0', line_name='line2', value=True)
    
    # set port1/line1 to "low"
    daq.digital_out_line(port_name='port1, line_name='line1', value=False)
    
    # read the line and save its value to `value`
    value = daq.digital_in_line(port_name='port1', line_name='line0')
    
    # change the analog out voltage level
    daq.analog_out(analog_output='ao1', voltage=1.2)
    
    # sample the analog input
    data = daq.sample_analog_in(analog_input='ai0',
                         sample_count=100, 
                         rate=1000.0)
    
    # retrieves the fundamental frequency that is present
    data = daq.sample_analog_in(analog_input='ai0',
                                sample_count=1000,
                                rate=1000)