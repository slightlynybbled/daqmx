from daqmx import NIDAQmxInstrument

# tested with NI USB-6001
# which has the following digital outputs:
#  - port0/line0 through line7
#  - port1/line0 through line3
#  - port2/line0

# first, we allocate the hardware using the automatic hardware allocation
# available to the instrument; this is safe when there is only one NIDAQmx
# instrument, but you may wish to specify a serial number or model number
# for a safer experience
daq = NIDAQmxInstrument()

print(daq)

# set the True or False state on the digital outputs by setting the
# `portX` and `lineX` attributes;
# use your multimeter to verify!
daq.port0.line0 = False
daq.port0.line1 = True

# you may wish to acquire the port separately and manipulate it directly
port = daq.port1
port.line0 = True

# if you try to set an output that doesn't exist, you
# should see errors (uncomment to see)
#port.line5 = True

# !!! IMPORTANT !!!!
# if you set the value of a port/line, the hardware will be changed to an
# output; however if you read the value using the similar syntax, the hardware
# will be changed to an input!
