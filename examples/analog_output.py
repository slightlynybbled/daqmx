from daqmx import NIDAQmxInstrument

# tested with NI USB-6001
# which has the following analog outputs:
#  - ao0
#  - ao1

# first, we allocate the hardware using the automatic hardware allocation
# available to the instrument; this is safe when there is only one NIDAQmx
# instrument, but you may wish to specify a serial number or model number
# for a safer experience
daq = NIDAQmxInstrument()

print(daq)

# set the voltage on the analog outputs by setting the attribute `aoX`;
# use your multimeter to verify!
daq.ao0 = 1.02
daq.ao1 = 2.04

# once the attribute is set, you should be able to read it on the daq; if the
# attribute hasn't been set, this will result in an error (for now)
print(f'ao0: {daq.ao0:.2f}V')

# if you set an attribute on an output that doesn't exist, then the attribute
# will be set on the object, but nothing will happen!  be sure that you are
# setting valid attributes
daq.ao2 = 3.0
print(daq.ao2)  # <-- there is no "ao2"!!!


