import PyDAQmx
import numpy as np
import ctypes
import time


class NIDAQmx:
    """
    This class will create the tasks and coordinate with the
    hardware in order to achieve a particular end on an input
    or output of the DAQ module.
    """
    command_timeout = 100
    sleep_time = 0.001

    def __init__(self, device_name=None, serial_number=None):
        """
        Allocates device hardware based on the device name or on the device serial number
        :param device_name: The enumerated device name of an attached device (i.e. 'Dev3')
        :param serial_number: The serial number as written on the product as a string (i.e. '1B5D935')
        """
        # todo: add access by model number
        self.device = device_name
        self.serial_number = serial_number

        if self.device:
            search = NIDAQmxSearch()
            devices = search.list_references()
            if self.device not in devices:
                raise ValueError('device name "{}" not found'.format(self.device))

        if serial_number and not self.device:
            search = NIDAQmxSearch()
            target_device = None
            for device in search.list_references():
                if search.product_serial_number(device) == int(serial_number, 16):
                    target_device = device
                    self.device = device

            if not target_device:
                raise ValueError('serial number {} does not correspond to an attached device')

        # when no specific device is specified, grab the first one
        if not device_name and not serial_number:
            search = NIDAQmxSearch()
            devices = search.list_references()
            if len(devices) == 1:
                self.device = devices[0]
            else:
                raise ValueError('serial number {} does not correspond to an attached device')

    def _validate(self, current_value, prefix):
        if isinstance(current_value, int):
            return prefix + str(current_value)
        else:
            return current_value.lower()

    def digital_out_line(self, port_name, line_name, value):
        """
        This method will set the specified dev/port/line to the specified value
        :param port_name: NI port designations (i.e. 'port0')
        :param line_name: NI line designations (i.e. 'line0')
        :param value: True or False
        :return: None
        """
        port_name = self._validate(port_name, 'port')
        line_name = self._validate(line_name, 'line')

        physical_channel = "{}/{}/{}".format(self.device, port_name, line_name).encode('utf-8')

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

    def digital_in_line(self, port_name, line_name):
        """
        This method will read the dev/port/line and return the value
        :param port_name: NI port designations (i.e. 'port0')
        :param line_name: NI line designations (i.e. 'line0')
        :return: True or False
        """
        port_name = self._validate(port_name, 'port')
        line_name = self._validate(line_name, 'line')

        physical_channel = "{}/{}/{}".format(self.device, port_name, line_name).encode('utf-8')

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

    def analog_out(self, analog_output, voltage=0.0):
        """
        This method will write the analog value to the specified dev/ao
        :param analog_output: NI analog output designation (i.e. 'ao0')
        :param voltage: A voltage in volts
        :return:
        """
        analog_output = self._validate(analog_output, 'ao')
        voltage = float(voltage)

        physical_channel = "{}/{}".format(self.device, analog_output).encode('utf-8')

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

    def sample_analog_in(self, analog_input, sample_count=1, rate=1000.0, output_format=None):
        """
        Sample an analog input <sample_count> number of times at <rate> Hz.
        :param analog_input: The NI analog input designation (i.e. 'ai0')
        :param sample_count: The number of desired samples (integer)
        :param rate: The sample rate in Hz
        :param output_format: The output format ('list', 'array', etc.)
        :return: The sample or samples as a numpy array
        """
        analog_input = self._validate(analog_input, 'ai')

        physical_channel = "{}/{}".format(self.device, analog_input).encode('utf-8')
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

    def get_fundamental_frequency(self, analog_input, sample_count=1000, rate=1000):
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


class NIDAQmxSearch:
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
        devices = list()

        for device in self.list_references():
            d = {
                'reference': device,
                'model': self.product_type(device),
                'serial': self.product_serial_number(device)
            }

            devices.append(d)

        return devices

    def list_references(self):
        """
        :return: A list of the attached devices, by name.
        """
        device_char_buffer = ctypes.create_string_buffer(self.STRING_BUF_LEN)
        PyDAQmx.DAQmxGetSysDevNames(device_char_buffer, self.STRING_BUF_LEN)

        devices = self._parse_c_str(device_char_buffer)
        devices = [device for device in devices if device is not '']

        return devices

    def list_serial_numbers(self):
        """
        :return: A list of the attached devices, by model number.
        """
        return [self.product_serial_number(device) for device in self.list_references()]

    def list_models(self):
        return [self.product_type(device) for device in self.list_references()]

    def product_type(self, device_name):
        """
        :param device_name: The enumerated device name of an attached device
        :return: The product type or model number
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
        :param device_name: The enumerated device name of an attached device
        :return: The product serial number
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
    ni_daq_search = NIDAQmxSearch()
    dev_list = ni_daq_search.list_references()

    print('ni search results: {}'.format(dev_list))
    print(ni_daq_search.list_do_lines(dev_list[0]))
    #print(ni_daq_search.list_ao(dev_list[0]))

    device = dev_list[0]

    daq = NIDAQmx(device)
    # daq.analog_out(analog_output='ao0', voltage=5.0)
    # daq.sample_analog_in(analog_input='ai0', sample_count=2)

    # daq.read_digital_line(port_name='port0')
    daq.digital_out_line(port_name='port0', line_name='line0', value=True)
    daq.analog_out('ao0', voltage=2.0)

    print(daq.sample_analog_in('ai0'))
    print(daq.sample_analog_in('ai0', sample_count=4))
    #print(daq.digital_in_line('port0', 'line0'))