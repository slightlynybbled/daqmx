from daqmx import NIDAQmxInstrument, AnalogInput

# tested with NI USB-6001
# which has the following analog inputs:
#  - ai0
#  - ai1
#  - ai2
#  - ai3

# first, we allocate the hardware using the automatic hardware allocation
# available to the instrument; this is safe when there is only one NIDAQmx
# instrument, but you may wish to specify a serial number or model number
# for a safer experience
daq = NIDAQmxInstrument()
print(daq)  # printing the instrument will result in showing the
            # device name, model number, and serial number

# you may also want to specify a particular device name, as assigned by
# the DAQmx interface; this is usually something like `Dev3`, although
# I believe that it may be renamed through the DAQmx interface
daq = NIDAQmxInstrument(device_name='Dev3')
print(daq)

# you might also simply wish to specify the model number to acquire
daq = NIDAQmxInstrument(model_number='USB-6001')
print(daq)

# further, you may wish to specify a particular serial number
daq = NIDAQmxInstrument(serial_number='1B5D996')  # <-- the serial number, as
print(daq)                                        # read off the back of the
                                                  # device in a hex format, is
                                                  # entered as a string

daq = NIDAQmxInstrument(serial_number=28694934)  # <-- this is the same device,
print(daq)                                       # entering the serial number
                                                 # as an integer instead of as
                                                 # a hex value

