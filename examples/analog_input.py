from daqmx import NIDAQmxInstrument, AnalogInput

# tested with NI USB-6001
# which has the following analog inputs:
#  - ai0
#  - ai1
#  - ai2
#  - ai3

# first, we allocate the hardware using the automatic hardware
# allocation available to the instrument; this is safe when there
# is only one NIDAQmx instrument, but you may wish to specify a
# serial number or model number for a safer experience
daq = NIDAQmxInstrument()

print(daq)

# the easiest way to get a single sample is to select the analog input
# attribute on the daq and interrogate its `value` attribute
print(f'daq.ai0.value: {daq.ai0.value:.3f}V')
print(f'daq.ai1.value: {daq.ai1.value:.3f}V')
print(f'daq.ai2.value: {daq.ai2.value:.3f}V')
print(f'daq.ai3.value: {daq.ai3.value:.3f}V')

# you will start throwing errors if you interrogate
# inputs that don't exist on the device (uncomment to see!)
#print(f'daq.ai4.value: {daq.ai4.value:.3f}V')

# for more nuanced control over the analog
# input, we could use the `capture` method
values = daq.ai1.capture(
    sample_count=10, rate=100,
    max_voltage=10.0, min_voltage=-10.0,
    mode='differential', timeout=3.0
)
print(f'values: {values} V')

# note that the values come back as type `numpy.ndarray`
print(f'type(values): {type(values)}')

# if you already know your device name, you might be
# happier going straight to the `AnalogInput` constructor:
ai0 = AnalogInput(device='Dev3', analog_input='ai0')

# we can do anything that we could have
# done previously with the daq.aiX
print(f'ai0.value: {ai0.value:.3f}V')
