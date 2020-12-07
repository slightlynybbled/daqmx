API
---

Instrument
==========

The :code:`NIDAQmxInstrument` class is the primary method through which most users will
acquire hardware.

.. autoclass:: daqmx.NIDAQmxInstrument
    :members:

Port
====

The :code:`Port` class is the class which implements port writes and reads.  It
may be used directly or through the instrument.

.. autoclass:: daqmx.Port
    :members:

Analog Input
============

The :code:`AnalogInput` class is the class which implements most of the
analog input functionality.  It may be used directly or through the instrument.

.. autoclass:: daqmx.AnalogInput
    :members:
