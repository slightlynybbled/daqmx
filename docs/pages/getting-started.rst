Getting Started
---------------

Install the Drivers
===================

Download an install the latest published
`NI DAQmx <https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html>`_
software from the National Instruments site.  This should install all necessary
hardware drivers into your OS.

Attach Hardware
===============

Attach your device to your PC.  Ensure tha the DAQmx software on your PC
has detected the hardware and assigned it a valid name (i.e. "Dev3").

Acquire Hardware
================

From within your program, acquire the hardware:

.. code-block:: python

    daq = NIDAQmxInstrument()

You may also specify the DAQmx-assigned name in order to acquire a specific
instrument:

.. code-block:: python

    daq = NIDAQmxInstrument(device_name='Dev3')

Hardware acquisition from the model number is also supported:

.. code-block:: python

    daq = NIDAQmxInstrument(model_number='USB-6001')

Finally, you may specify the serial number:

.. code-block:: python

    daq = NIDAQmxInstrument(serial_number='1B5D996')

Sample Analog Input
===================

Read analog input 0, print it to the console:

.. code-block:: python

    print(f'daq.ai0.value: {daq.ai0.value:.3f}V')

Capture Analog Input
====================

Take multiple analog samples with more control over the hardware:

.. code-block:: python

    values = daq.ai1.capture(
        sample_count=10, rate=100,
        max_voltage=10.0, min_voltage=-10.0,
        mode='differential', timeout=3.0
    )
    print(values)

Note that the :code:`values` variable contains a numpy array which represents
all samples acquired during the capture process.
