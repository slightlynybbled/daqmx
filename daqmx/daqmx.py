from dataclasses import dataclass
import logging

import PyDAQmx
import numpy as np
import ctypes
import time


__version__ = '0.3.0'


def __format(current_value: (int, str), prefix: str):
    """
    Convenience function to add consistency throughout the object.

    :param current_value: a numeric string or integer
    :param prefix: the string prefix, such as "port" or "line"
    :return: the formatted string, such as "port0" or "line1"
    """
    if isinstance(current_value, int):
        return prefix + str(current_value)
    else:
        return current_value.lower()


def __validate_ao(device: str, analog_output: str):
    """
    Ensure that the specified analog output exists on the device.  This
    method will raise a ValueError if the line specified is invalid.

    :param analog_output: the string that specifies
        the analog output (i.e. "ao0")
    :return: None
    """
    searcher = _NIDAQmxSearcher()
    valid_aos = [ao.replace(f'{device}/', '')
                 for ao in searcher.list_ao(device)]
    if analog_output not in valid_aos:
        raise ValueError(f'the analog output "{analog_output}" not found; '
                         f'valid analog outputs for {device} '
                         f'are: {", ".join(valid_aos)}')


def analog_out(device: str, analog_output: str, voltage: (int, float) = 0.0):
    """
    This method will write the analog value to the specified dev/ao

    :param device: the NI device reference (i.e. 'Dev3')
    :param analog_output: the NI analog output designation (i.e. 'ao0')
    :param voltage: the desired voltage in volts
    :return: None
    """
    analog_output = __format(analog_output, 'ao')
    __validate_ao(device, analog_output)

    voltage = float(voltage)

    physical_channel = f"{device}/{analog_output}".encode('utf-8')

    task = PyDAQmx.Task()
    task.CreateAOVoltageChan(physical_channel,
                             ''.encode('utf-8'),
                             -10.0,
                             10.0,
                             PyDAQmx.DAQmx_Val_Volts,
                             None)

    autostart = 1
    timeout = 10.0

    task.StartTask()
    task.WriteAnalogScalarF64(autostart,
                              timeout,
                              voltage,
                              None)

    task.StopTask()


class NIDAQmxInstrument:
    """
    This class will create the tasks and coordinate with the
    hardware in order to achieve a particular end on an input
    or output of the DAQ module.

    The methods within this object utilize the concepts found in the
    NI-DAQmx Help menu, such as channels and tasks.

    :param device_name: the device name, often formatted like `Dev3`
    :param serial_number: the serial number as a hexadecimal value (this is
        usually what is printed on the label)
    :param model_number: the model number as printed on the label
    """
    command_timeout = 100
    sleep_time = 0.001

    def __init__(self, device_name: str = None,
                 serial_number: str = None,
                 model_number: str = None,
                 loglevel=logging.INFO):

        searcher = _NIDAQmxSearcher()

        if device_name:
            devices = searcher.list_devices()
            if device_name not in devices:
                raise ValueError(f'device name "{device_name}" not found; '
                                 f'valid devices: {", ".join(devices)}')
            device = device_name
        elif serial_number:
            device = searcher.device_lookup_by_sn(int(serial_number, 16))
        elif model_number:
            device = searcher.device_lookup_by_model_number(model_number)

        else:  # when no specific device is specified, grab the first one
            devices = searcher.list_devices()
            if len(devices) == 0:
                raise ValueError('no devices found')
            elif len(devices) == 1:
                device = devices[0]
            else:
                raise ValueError('multiple devices found')

        # todo: uses setattr to add attributes to a class at runtime
        analog_outputs = [ao.split('/')[1] for ao in searcher.list_ao(device)]

        #digital_outputs = [f'{do.split("/")[1]}/{do.split("/")[2]}' for do in searcher.list_do_lines(device)]
        digital_outputs = []
        for do in searcher.list_do_lines(device):
            _, port, line = do.split('/')

        outputs = analog_outputs + digital_outputs

        print(outputs)

        self._outputs = outputs
        self._device = device
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

    def __setattr__(self, attr, value):
        # todo: trying to make hardware attributes more "pythonic"
        if 'ao' in attr and self.__check_for_io(attr):
            analog_out(self._device, attr, value)
        if 'port' in attr and self.__check_for_io(attr):
            print('port is being set:', attr, value)

        self.__dict__[attr] = value

    @property
    def sn(self):
        """
        Returns the device serial number

        :return: the device serial number
        """
        return _NIDAQmxSearcher().product_serial_number(self._device)

    def __check_for_io(self, io_name):
        if io_name in self._outputs:
            return True
        else:
            return False

    def __format(self, current_value: (int, str), prefix: str):
        """
        Convenience function to add consistency throughout the object.

        :param current_value: a numeric string or integer
        :param prefix: the string prefix, such as "port" or "line"
        :return: the formatted string, such as "port0" or "line1"
        """
        if isinstance(current_value, int):
            return prefix + str(current_value)
        else:
            return current_value.lower()

    def __validate_line(self, line_string: str):
        """
        Ensure that the specified digital line exists on the device.  This
        method will raise a ValueError if the line specified is invalid.

        :param line_string: the string that specifies the specific line (i.e. "port0/line3")
        :return: None
        """
        searcher = _NIDAQmxSearcher()
        valid_lines = [line.replace(f'{self._device}/', '')
                     for line in searcher.list_do_lines(self._device)]
        if line_string not in valid_lines:
            raise ValueError(f'the analog input "{line_string}" not found; '
                             f'valid analog outputs for {self._device} '
                             f'are: {", ".join(valid_lines)}')

    def __validate_ai(self, analog_input: str):
        """
        Ensure that the specified analog input exists on the device.  This
        method will raise a ValueError if the line specified is invalid.

        :param analog_input: the string that specifies
            the analog input (i.e. "ai1")
        :return: None
        """
        searcher = _NIDAQmxSearcher()
        valid_ais = [ai.replace(f'{self._device}/', '')
                     for ai in searcher.list_ai(self._device)]
        if analog_input not in valid_ais:
            raise ValueError(f'the analog input "{analog_input}" not found; '
                             f'valid analog outputs for {self._device} '
                             f'are: {", ".join(valid_ais)}')

    def __validate_ao(self, analog_output: str):
        """
        Ensure that the specified analog output exists on the device.  This
        method will raise a ValueError if the line specified is invalid.

        :param analog_output: the string that specifies
            the analog output (i.e. "ao0")
        :return: None
        """
        searcher = _NIDAQmxSearcher()
        valid_aos = [ao.replace(f'{self._device}/', '')
                     for ao in searcher.list_ao(self._device)]
        if analog_output not in valid_aos:
            raise ValueError(f'the analog output "{analog_output}" not found; '
                             f'valid analog outputs for {self._device} '
                             f'are: {", ".join(valid_aos)}')

    def digital_out_line(self, port_name: str, line_name: str, value: bool):
        """
        This method will set the specified dev/port/line to the specified value

        :param port_name: the NI port designations (i.e. 'port0')
        :param line_name: the NI line designations (i.e. 'line0')
        :param value: True if the line is to be held "high" else False
        :return: None
        """
        port_name = self.__format(port_name, 'port')
        line_name = self.__format(line_name, 'line')

        line = f'{port_name}/{line_name}'
        self.__validate_line(line)

        physical_channel = f"{self._device}/{line}".encode('utf-8')

        task = PyDAQmx.Task()
        task.CreateDOChan(physical_channel,
                          ''.encode('utf-8'),
                          PyDAQmx.DAQmx_Val_ChanForAllLines)

        if value:
            data = np.array([1], dtype=np.uint8)
        else:
            data = np.array([0], dtype=np.uint8)
        samples_written = PyDAQmx.int32()

        autostart = 1
        timeout = 10.0

        task.StartTask()
        task.WriteDigitalLines(1,
                               autostart,
                               timeout,
                               PyDAQmx.DAQmx_Val_GroupByChannel,
                               data,
                               PyDAQmx.byref(samples_written),
                               None)

        task.StopTask()

    def digital_in_line(self, port_name: str, line_name: str) -> bool:
        """
        This method will read the dev/port/line and return the value

        :param port_name: the NI port designations (i.e. 'port0')
        :param line_name: the NI line designations (i.e. 'line0')
        :return: True if input is "high" else False
        """
        port_name = self.__format(port_name, 'port')
        line_name = self.__format(line_name, 'line')

        line = f'{port_name}/{line_name}'
        self.__validate_line(line)

        physical_channel = f"{self._device}/{line}".encode('utf-8')

        task = PyDAQmx.Task()

        start_time = time.clock()
        success = False

        while not success:
            try:
                task.CreateDIChan(physical_channel,
                                  ''.encode('utf-8'),
                                  PyDAQmx.DAQmx_Val_ChanForAllLines)
                success = True
            except PyDAQmx.DAQError as e:
                if (time.clock() - start_time) > self.command_timeout:
                    return None

                time.sleep(self.sleep_time)

        data = np.array([1], dtype=np.uint8)
        samples_written = PyDAQmx.int32()

        samples_per_channel = 1
        timeout = 10.0

        task.StartTask()
        task.ReadDigitalLines(samples_per_channel,
                              timeout,
                              PyDAQmx.DAQmx_Val_GroupByChannel,
                              data,
                              1,
                              None,
                              None,
                              None)

        task.StopTask()

        if data == [1]:
            return True
        else:
            return False

    def analog_out(self, analog_output: str, voltage: (int, float) = 0.0):
        """
        This method will write the analog value to the specified dev/ao

        :param analog_output: the NI analog output designation (i.e. 'ao0')
        :param voltage: the desired voltage in volts
        :return: None
        """
        analog_output = self.__format(analog_output, 'ao')
        self.__validate_ao(analog_output)

        voltage = float(voltage)

        physical_channel = f"{self._device}/{analog_output}".encode('utf-8')

        task = PyDAQmx.Task()
        task.CreateAOVoltageChan(physical_channel,
                                 ''.encode('utf-8'),
                                 -10.0,
                                 10.0,
                                 PyDAQmx.DAQmx_Val_Volts,
                                 None)

        autostart = 1
        timeout = 10.0

        task.StartTask()
        task.WriteAnalogScalarF64(autostart,
                                  timeout,
                                  voltage,
                                  None)

        task.StopTask()

    def sample_analog_in(self, analog_input: str,
                         sample_count: int = 1, rate: (int, float) = 1000.0,
                         output_format: str = None):
        """
        Sample an analog input <sample_count> number of times at <rate> Hz.

        :param analog_input: the NI analog input designation (i.e. 'ai0')
        :param sample_count: the number of desired samples (integer)
        :param rate: the sample rate in Hz
        :param output_format: the output format ('list', 'array', etc.)
        :return: the sample or samples as a numpy array
        """
        analog_input = self.__format(analog_input, 'ai')
        self.__validate_ai(analog_input)

        physical_channel = f"{self._device}/{analog_input}".encode('utf-8')
        num_of_samples_read = PyDAQmx.int32()
        data = np.zeros(sample_count, dtype=np.float64)

        task = PyDAQmx.Task()
        task.CreateAIVoltageChan(physical_channel,
                                 "",
                                 PyDAQmx.DAQmx_Val_Diff,
                                 -10.0, 10.0,
                                 PyDAQmx.DAQmx_Val_Volts,
                                 None)

        if sample_count > 1:
            task.CfgSampClkTiming("",
                                  rate,
                                  PyDAQmx.DAQmx_Val_Rising,
                                  PyDAQmx.DAQmx_Val_FiniteSamps,
                                  sample_count)

        task.StartTask()
        task.ReadAnalogF64(sample_count,
                           10.0,
                           PyDAQmx.DAQmx_Val_GroupByChannel,
                           data,
                           sample_count,
                           PyDAQmx.byref(num_of_samples_read),
                           None)

        if not output_format:
            return data
        elif output_format == 'list':
            return list(data)
        else:
            raise ValueError('output_format must be "list" or left blank')

    def get_fundamental_frequency(self, analog_input: str,
                                  sample_count: int = 1000,
                                  rate: (int, float) = 1000):
        """
        Acquires the fundamental frequency observed within the samples

        :param analog_input: the NI analog input designation (i.e. 'ai0')
        :param sample_count: the number of samples to acquired
        :param rate: the sample rate in Hz
        :return:
        """
        analog_input = self.__format(analog_input, 'ai')
        self.__validate_ai(analog_input)

        signal = self.sample_analog_in(analog_input, sample_count, rate)
        fourier = np.fft.fft(signal)
        n = signal.size
        timestep = 1 / rate

        freq = np.fft.fftfreq(n, d=timestep)

        # make a series of tuples that couple the
        # absolute magnitude with the frequency
        a_vs_f = []
        for i, e in enumerate(freq):
            a_vs_f.append((np.absolute(fourier[i]), freq[i]))

        # sort based on the absolute magnitude
        a_vs_f_sorted = sorted(a_vs_f, key=lambda x: x[0])

        # if the highest magnitude is at 0.0 frequency,
        # then remove that datapoint
        if a_vs_f_sorted[-1][1] == 0.0:
            a_vs_f_sorted.pop(-1)

        # the highest magnitude is at the last index
        frequency = a_vs_f_sorted[-1][1]
        if frequency < 0:
            frequency *= -1

        frequency = round(float(frequency), 1)

        return frequency


class _NIDAQmxSearcher:
    """
    This class is used to search the currently connected devices
    """
    STRING_BUF_LEN = 500

    def __init__(self):
        """
        No initialization requirements
        """
        pass

    def _parse_c_str(self, c_string_buffer):
        """
        Helper function to assist in parsing c strings
        :param c_string_buffer: a string with comma-separated values
        :return: a tuple of strings that were once separated by commas in a single string
        """
        items = c_string_buffer.value.decode('utf-8').split(',')
        items = [item.strip() for item in items]
        return tuple(items)

    def list_devices(self):
        """
        :return: a list of the attached devices, by name
        """
        device_char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)
        PyDAQmx.DAQmxGetSysDevNames(device_char_buffer, self.STRING_BUF_LEN)

        devices = self._parse_c_str(device_char_buffer)
        devices = [device for device in devices if device is not '']

        return devices

    def list_serial_numbers(self):
        """
        Return a list of serial numbers that are attached to the machine.

        :return: a list of the attached devices, by model number.
        """
        return [self.product_serial_number(device) for device in self.list_devices()]

    def list_models(self):
        """
        Return a list of models that are attached to the machine

        :return: a list of all model numbers that are attached
        """

        return list(set([self.model_number(device) for device in self.list_devices()]))

    def model_number(self, device_name):
        """
        Return a product type (model number) given the device name

        :param device_name: the enumerated device name of an attached device
            (i.e. "Dev3")
        :return: the product type or model number
        """
        dev = device_name.encode('utf-8')
        dev_char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)

        # save the device name into the character buffer
        for i, c in enumerate(dev):
            dev_char_buffer[i] = c

        char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)
        PyDAQmx.DAQmxGetDevProductType(ctypes.addressof(dev_char_buffer), char_buffer, self.STRING_BUF_LEN)

        product_type = self._parse_c_str(char_buffer)[0]

        return product_type

    def product_serial_number(self, device_name):
        """
        Return the product serial number of the specified device.

        :param device_name: the enumerated device name of an attached device (i.e. "Dev3")
        :return: the product serial number
        """
        dev = device_name.encode('utf-8')
        dev_char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)

        # save the device name into the character buffer
        for i, c in enumerate(dev):
            dev_char_buffer[i] = c

        num_buffer = ctypes.c_uint32(0)
        PyDAQmx.DAQmxGetDevSerialNum(ctypes.addressof(dev_char_buffer), num_buffer)

        product_sn = num_buffer.value

        return product_sn

    def device_lookup_by_sn(self, serial_number: (str, int)):
        """
        Lookup a device name that is currently connected to the PC by serial
        number.  Note that many National Instruments devices print serial
        numbers in hexadecimal!

        :param serial_number: a string or integer value that can be read from
            the device label
        :return: the attached device that matches the serial number
        """
        devices = self.list_devices()
        for device in devices:
            if self.product_serial_number(device) == serial_number:
                return device

    def device_lookup_by_model_number(self, model_number: str):
        """
        Lookup a device name that is currently connected to the PC by model
        number.  Note that, if there are multiple devices of the same model
        number connected to the PC, then this function will return the first
        instance encountered.

        :param model_number: a string that can be read from the device label
        :return: the first attached device that matches the model number
        """
        devices = self.list_devices()
        for device in devices:
            if self.model_number(device) == model_number:
                return device

    def list_ai(self, device_name):
        """
        :param device_name: The enumerated device name of an attached device
        :return: All analog inputs present on the device
        """
        dev = device_name.encode('utf-8')
        dev_char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)

        # save the device name into the character buffer
        for i, c in enumerate(dev):
            dev_char_buffer[i] = c

        char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)
        PyDAQmx.DAQmxGetDevAIPhysicalChans(ctypes.addressof(dev_char_buffer), char_buffer, self.STRING_BUF_LEN)

        ais = self._parse_c_str(char_buffer)

        return ais

    def list_ao(self, device_name):
        """
        :param device_name: The enumerated device name of an attached device
        :return: All analog outputs present on the device
        """
        dev = device_name.encode('utf-8')
        dev_char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)

        # save the device name into the character buffer
        for i, c in enumerate(dev):
            dev_char_buffer[i] = c

        char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)
        PyDAQmx.DAQmxGetDevAOPhysicalChans(ctypes.addressof(dev_char_buffer), char_buffer, self.STRING_BUF_LEN)

        aos = self._parse_c_str(char_buffer)

        return aos

    def list_do_lines(self, device_name):
        """
        :param device_name: The enumerated device name of an attached device
        :return: All digital output lines on the device
        """
        dev = device_name.encode('utf-8')
        dev_char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)

        # save the device name into the character buffer
        for i, c in enumerate(dev):
            dev_char_buffer[i] = c

        char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)
        PyDAQmx.DAQmxGetDevDOLines(ctypes.addressof(dev_char_buffer), char_buffer, self.STRING_BUF_LEN)

        do_lines = self._parse_c_str(char_buffer)

        return do_lines


if __name__ == "__main__":
    daq = NIDAQmxInstrument(device_name='Dev3')



    daq.ao0 = 4.5
    daq.ao1 = 2.6

    daq.port0 = True

    print(daq.__dict__)

    # # daq.analog_out(analog_output='ao0', voltage=5.0)
    # # daq.sample_analog_in(analog_input='ai0', sample_count=2)
    #
    # # daq.read_digital_line(port_name='port0')
    # daq.digital_out_line(port_name='port0', line_name='line0', value=True)
    # daq.analog_out('ao0', voltage=2.0)
    #
    # print(daq.sample_analog_in('ai0'))
    # print(daq.sample_analog_in('ai0', sample_count=4))
    # #print(daq.digital_in_line('port0', 'line0'))