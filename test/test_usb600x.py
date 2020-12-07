"""
This files is for testing the National Instruments USB-600x series of data
acquisition devices.  To execute this test, the device must be attached to
the PC and the following connections must be made:

 - port0.line0 to port1.line0
 - port0.line1 to port1.line1
 - ao0 to (ai0+ and ai1)
 - ao1 to (ai0- and ai5)

Only one of the USB NI-600x device should be connected to the PC at the time
of the test.  If the `device_model_number` is different that what is connected
to the PC, the test may fail.

The testing that will occur will look something like this:

 - port0.line0 to True, read port1.line0, ensure is True
 - port0.line0 to False, read port1.line0, ensure is False
 - port0.line1 to True, read port1.line1, ensure is True
 - port0.line1 to False, read port1.line1, ensure is False
 - ao0 to 2.5V, confirm with ai1 (single-ended ground-referenced measurement)
 - ao1 to 2.5V, confirm with ai5 (single-ended ground-referenced measurement)
 - confirm ai0 differential measurement of 0.0V
 - change ao0 to 3.5V, confirm ai0 different measurement of 1.0V
 - repeat analog sequence on ao1
"""
import pytest
from daqmx import NIDAQmxInstrument

device_model_number = 'USB-6001'


@pytest.fixture
def daq():
    instrument = NIDAQmxInstrument(model_number=device_model_number)

    # configure port0.line0 and line1 to inputs
    instrument.port0.line0
    instrument.port0.line1

    # configure ao lines to 0V
    instrument.ao0 = 0
    instrument.ao1 = 0

    yield instrument


def test_hardware_acquisition(daq):
    assert True


def test_dio0_true(daq):
    """
    Change state of port0.line0, port0.line1, then
    reads those lines using port1.

    :param daq: the NIDAQmxInstrument instance
    :return:
    """
    daq.port0.line0 = True
    daq.port0.line1 = False

    assert daq.port1.line0 == True
    assert daq.port1.line1 == False


def test_dio0_false(daq):
    """
    Change state of port0.line0, port0.line1, then
    reads those lines using port1.

    :param daq: the NIDAQmxInstrument instance
    :return:
    """
    daq.port0.line0 = False
    daq.port0.line1 = True

    assert daq.port1.line0 == False
    assert daq.port1.line1 == True


def test_dio1_true(daq):
    """
    Change state of port1.line0, port1.line1, then
    reads those lines using port0.

    :param daq: the NIDAQmxInstrument instance
    :return:
    """
    daq.port1.line0 = True
    daq.port1.line1 = False

    assert daq.port0.line0 == True
    assert daq.port0.line1 == False


def test_dio1_false(daq):
    """
    Change state of port1.line0, port1.line1, then
    reads those lines using port0.

    :param daq: the NIDAQmxInstrument instance
    :return:
    """
    daq.port1.line0 = False
    daq.port1.line1 = True

    assert daq.port0.line0 == False
    assert daq.port0.line1 == True


def test_dio_error(daq):
    """
    Ensure errors are thrown when bad input given to DO

    :param daq: the NIDAQmxInstrument instance
    :return:
    """
    with pytest.raises(ValueError):
        daq.port1.line0 = 0
    with pytest.raises(ValueError):
        daq.port1.line0 = 1
    with pytest.raises(ValueError):
        daq.port1.line0 = 0.0
    with pytest.raises(ValueError):
        daq.port1.line0 = 1.0

    daq.port1.line0 = False


def test_ai0_diff(daq):
    # set to near 0.0V differential
    daq.ao0 = 2.5
    daq.ao1 = 2.5

    # check 100 samples, ensure that they are all close to the expected value
    for value in daq.ai0.capture(sample_count=100):
        if value > 0.01 or value < -0.01:
            assert False

    # set to 1.0V differential
    daq.ao0 = 3.0
    daq.ao1 = 2.0
    for value in daq.ai0.capture(sample_count=100):
        if value > 1.01 or value < 0.99:
            assert False

    # set to -1.0V differential
    daq.ao0 = 2.0
    daq.ao1 = 3.0
    for value in daq.ai0.capture(sample_count=100):
        if value > -0.99 or value < -1.01:
            assert False


def test_analog_input_diff(daq):
    # set to near 0.0V differential
    daq.ao0 = 2.5
    daq.ao1 = 2.5

    # check 100 samples, ensure that they are all close to the expected value
    for value in daq.ai1.capture(sample_count=100):
        if value > 0.01 or value < -0.01:
            assert False

    # set to 1.0V differential
    daq.ao0 = 3.0
    daq.ao1 = 2.0
    for value in daq.ai1.capture(sample_count=100):
        if value > 1.01 or value < 0.99:
            assert False

    # set to -1.0V differential
    daq.ao0 = 2.0
    daq.ao1 = 3.0
    for value in daq.ai1.capture(sample_count=100):
        if value > -0.99 or value < -1.01:
            assert False


def test_analog_input_single(daq):
    """
    Applies several voltage combinations to ai1 and ai5 single-ended inputs
    and ensures that they are as expected.

    :param daq:
    :return:
    """
    num_of_samples = 10
    values_to_test = [
        (2.5, 2.5),
        (1.5, 3.5),
        (3.5, 1.5),
        (0.5, 4.5),
        (4.5, 0.5),
        (2, 3),     # using an integer to set instead of a float
      ]
    tolerance = 0.005

    for v0, v1 in values_to_test:
        daq.ao0 = v0
        daq.ao1 = v1

        values = daq.ai1.capture(sample_count=num_of_samples, mode='single-ended referenced')
        for value in values:
            if value > (v0+tolerance) or value < (v0-tolerance):
                assert False

        values = daq.ai5.capture(sample_count=num_of_samples, mode='single-ended referenced')
        for value in values:
            if value > (v1+tolerance) or value < (v1-tolerance):
                assert False


def test_errors_input_doesnt_exist(daq):
    with pytest.raises(ValueError):
        daq.port1.line5 = True

    with pytest.raises(ValueError):
        daq.port0.line8 = True

    with pytest.raises(ValueError):
        print(daq.port1.line4)
