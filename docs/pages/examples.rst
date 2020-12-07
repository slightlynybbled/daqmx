Examples
========

Hardware Acquisition
---------------------

.. code-block:: python

    from daqmx import NIDAQmxInstrument

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

Read Digital Input
------------------

.. code-block:: python

    from daqmx import NIDAQmxInstrument

    # tested with NI USB-6001
    # which has the following digital inputs:
    #  - port0/line0 through line7
    #  - port1/line0 through line3
    #  - port2/line0

    # first, we allocate the hardware using the automatic hardware
    # allocation available to the instrument; this is safe when there
    # is only one NIDAQmx instrument, but you may wish to specify a
    # serial number or model number for a safer experience
    daq = NIDAQmxInstrument()

    print(daq)

    # read the True or False state on the digital outputs
    # by reading the `portX` and `lineX` attributes; you
    # may wish to use the 5V output available to force the
    # pin to a state
    print(daq.port0.line0)
    print(daq.port0.line1)

    # !!! IMPORTANT !!!!
    # if you set the value of a port/line, the hardware will
    # be changed to an output; however if you read the value
    # using the similar syntax, the hardware will be changed
    # to an input!

Set/Clear Digital Output
------------------------

.. code-block:: python

    from daqmx import NIDAQmxInstrument

    # tested with NI USB-6001
    # which has the following digital outputs:
    #  - port0/line0 through line7
    #  - port1/line0 through line3
    #  - port2/line0

    # first, we allocate the hardware using the automatic hardware
    # allocation available to the instrument; this is safe when there
    # is only one NIDAQmx instrument, but you may wish to specify a
    # serial number or model number for a safer experience
    daq = NIDAQmxInstrument()

    print(daq)

    # set the True or False state on the digital outputs by setting the
    # `portX` and `lineX` attributes;
    # use your multimeter to verify!
    daq.port0.line0 = False
    daq.port0.line1 = True

    # you may wish to acquire the port separately
    # and manipulate it directly
    port = daq.port1
    port.line0 = True

    # if you try to set an output that doesn't exist, you
    # should see errors (uncomment to see)
    #port.line5 = True

    # !!! IMPORTANT !!!!
    # if you set the value of a port/line, the hardware will
    # be changed to an output; however if you read the value
    # using the similar syntax, the hardware will be changed
    # to an input!

Read Analog Input
-----------------

.. code-block:: python

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

Write Analog Output
-------------------

.. code-block:: python

    from daqmx import NIDAQmxInstrument

    # tested with NI USB-6001
    # which has the following analog outputs:
    #  - ao0
    #  - ao1

    # first, we allocate the hardware using the automatic hardware
    # allocation available to the instrument; this is safe when there
    # is only one NIDAQmx instrument, but you may wish to specify a
    # serial number or model number for a safer experience
    daq = NIDAQmxInstrument()

    print(daq)

    # set the voltage on the analog outputs by setting the
    # attribute `aoX`; use your multimeter to verify!
    daq.ao0 = 1.02
    daq.ao1 = 2.04

    # once the attribute is set, you should be able to read
    # it on the daq; if the attribute hasn't been set, this
    # will result in an error (for now)
    print(f'ao0: {daq.ao0:.2f}V')

    # if you set an attribute on an output that doesn't exist,
    # then the attribute will be set on the object, but nothing
    # will happen!  be sure that you are setting valid attributes
    daq.ao2 = 3.0
    print(daq.ao2)  # <-- there is no "ao2"!!!
