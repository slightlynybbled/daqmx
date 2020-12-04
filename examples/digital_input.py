from daqmx import NIDAQmxInstrument

# tested with NI USB-6001
# which has the following digital inputs:
#  - port0/line0 through line7
#  - port1/line0 through line3
#  - port2/line0

# first, we allocate the hardware using the automatic hardware allocation
# available to the instrument; this is safe when there is only one NIDAQmx
# instrument, but you may wish to specify a serial number or model number
# for a safer experience
daq = NIDAQmxInstrument()

print(daq)

# read the True or False state on the digital outputs by reading the
# `portX` and `lineX` attributes; you may wish to use the 5V output available
# to force the pin to a state
print(daq.port0.line0)
print(daq.port0.line1)

# !!! IMPORTANT !!!!
# if you set the value of a port/line, the hardware will be changed to an
# output; however if you read the value using the similar syntax, the hardware
# will be changed to an input!
