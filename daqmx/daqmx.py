from dataclasses import dataclass
import logging

import numpy as np
import ctypes
import time


_logger = logging.getLogger(__name__)

# put a try/except here so that documentation may be built on
# remote servers without autodoc causing an issue
try:
    import PyDAQmx
except NotImplementedError as e:
    _logger.warning(e)
    _logger.warning('"PyDAQmx" is raising an error.  You can '
                    'build documentation, but you likely have '
                    'issues with your installation.')


def _format(current_value: (int, str), prefix: str):
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


def _validate_ao(device: str, analog_output: str):
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


def _validate_line(device: str, line_string: str):
    """
    Ensure that the specified digital line exists on the device.  This
    method will raise a ValueError if the line specified is invalid.

    :param line_string: the string that specifies the specific line (i.e. "port0/line3")
    :return: None
    """
    searcher = _NIDAQmxSearcher()
    valid_lines = [line.replace(f'{device}/', '')
                 for line in searcher.list_do_lines(device)]
    if line_string not in valid_lines:
        raise ValueError(f'the analog input "{line_string}" not found; '
                         f'valid analog outputs for {device} '
                         f'are: {", ".join(valid_lines)}')


def _validate_ai(device, analog_input: str):
    """
    Ensure that the specified analog input exists on the device.  This
    method will raise a ValueError if the line specified is invalid.

    :param device: the device string (i.e. 'Dev3')
    :param analog_input: the string that specifies
        the analog input (i.e. "ai1")
    :return: None
    """
    searcher = _NIDAQmxSearcher()
    valid_ais = [ai.replace(f'{device}/', '')
                 for ai in searcher.list_ai(device)]
    if analog_input not in valid_ais:
        raise ValueError(f'the analog input "{analog_input}" not found; '
                         f'valid analog outputs for {device} '
                         f'are: {", ".join(valid_ais)}')


def _analog_out(device: str, analog_output: str, voltage: (int, float) = 0.0):
    """
    This method will write the analog value to the specified dev/ao

    :param device: the NI device reference (i.e. 'Dev3')
    :param analog_output: the NI analog output designation (i.e. 'ao0')
    :param voltage: the desired voltage in volts
    :return: None
    """
    analog_output = _format(analog_output, 'ao')
    _validate_ao(device, analog_output)

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


def _digital_out_line(device: str, port_name: str, line_name: str, value: bool):
    """
    This method will set the specified dev/port/line to the specified value

    :param port_name: the NI port designations (i.e. 'port0')
    :param line_name: the NI line designations (i.e. 'line0')
    :param value: True if the line is to be held "high" else False
    :return: None
    """
    port_name = _format(port_name, 'port')
    line_name = _format(line_name, 'line')

    line = f'{port_name}/{line_name}'
    _validate_line(device, line)

    physical_channel = f"{device}/{line}".encode('utf-8')

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


def _digital_in_line(device: str, port_name: str, line_name: str) -> bool:
    """
    This method will read the dev/port/line and return the value

    :param device: the NI device designation (i.e. 'Dev3')
    :param port_name: the NI port designations (i.e. 'port0')
    :param line_name: the NI line designations (i.e. 'line0')
    :return: True if input is "high" else False
    """
    command_timeout = 100
    sleep_time = 0.001

    port_name = _format(port_name, 'port')
    line_name = _format(line_name, 'line')

    line = f'{port_name}/{line_name}'
    _validate_line(device, line)

    physical_channel = f"{device}/{line}".encode('utf-8')

    task = PyDAQmx.Task()

    start_time = time.perf_counter()
    success = False

    while not success:
        try:
            task.CreateDIChan(physical_channel,
                              ''.encode('utf-8'),
                              PyDAQmx.DAQmx_Val_ChanForAllLines)
            success = True
        except PyDAQmx.DAQError as e:
            if (time.perf_counter() - start_time) > command_timeout:
                raise TimeoutError

            time.sleep(sleep_time)

    data = np.array([1], dtype=np.uint8)

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
    return False


def _sample_analog_in(device: str,
                      analog_input: str,
                      sample_count: int = 1,
                      rate: (int, float) = 1000.0,
                      max_voltage: (int, float) = 5.0,
                      min_voltage: (int, float) = 0.0,
                      mode: str = 'differential',
                      timeout: (int, float) = None,
                      output_format: str = None):
    """
    Sample an analog input <sample_count> number of times at <rate> Hz.

    :param device: the NI device (i.e. "Dev3")
    :param analog_input: the NI analog input designation (i.e. 'ai0')
    :param sample_count: the number of desired samples (integer)
    :param rate: the sample rate in Hz
    :param max_voltage: the maximum voltage possible
    :param min_voltage: the minimum voltage range
    :param mode: the voltage mode of operation; choices: 'differential',
        'pseudo-differential', 'single-ended referenced',
        'single-ended non-referenced'
    :param timeout: the time at which the function should return if this
        time has elapsed; set to None to make infinite (default)
    :param output_format: the output format ('list', 'array', etc.)
    :return: the sample or samples as a numpy array
    """
    mode_lookup = {'differential': PyDAQmx.DAQmx_Val_Diff,
                   'pseudo-differential': PyDAQmx.DAQmx_Val_PseudoDiff,
                   'single-ended referenced': PyDAQmx.DAQmx_Val_RSE,
                   'single-ended non-referenced': PyDAQmx.DAQmx_Val_NRSE}

    if mode.lower() not in mode_lookup.keys():
        raise ValueError(f'mode "{mode}" not valid, expected values: {", ".join(mode_lookup.keys())}')

    if timeout is None or timeout < 1:
        timeout = -1

    analog_input = _format(analog_input, 'ai')
    _validate_ai(device, analog_input)

    physical_channel = f"{device}/{analog_input}".encode('utf-8')

    num_of_samples_read = PyDAQmx.int32()
    data = np.zeros(sample_count, dtype=np.float64)

    task = PyDAQmx.Task()
    task.CreateAIVoltageChan(physical_channel,
                             "",
                             mode_lookup[mode],
                             min_voltage, max_voltage,
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
                       timeout,
                       PyDAQmx.DAQmx_Val_GroupByChannel,
                       data,
                       sample_count,
                       PyDAQmx.byref(num_of_samples_read),
                       None)

    if sample_count != num_of_samples_read.value:
        raise RuntimeWarning(f'the number of samples returned '
                             f'({num_of_samples_read}) does not match '
                             f'the number of samples requested '
                             f'({sample_count})')

    if not output_format:
        return data
    elif output_format == 'list':
        return list(data)
    else:
        raise ValueError('output_format must be "list" or left blank')


class AnalogInput:
    """
    Represents an analog input on the DAQmx device.

    :param device: the device string assigned by DAQmx (i.e. 'Dev3)
    :param analog_input: the analog input name assigned by DAQmx (i.e. "ao0")
    :param sample_count: the number of samples to take
    :param rate: the frequency at which to sample the input
    :param max_voltage: the maximum expected voltage
    :param min_voltage: the minimum expected voltage
    :param mode: the mode; valid values: differential, pseudo-differential, /
        singled-ended referenced, singled-ended non-referenced
    :param timeout: the time at which an error will occur if no response /
        from the instrument is received.
    """
    def __init__(self, device: str, analog_input: str = None,
                 sample_count: int = 1000, rate: (int, float) = 1000.0,
                 max_voltage: (int, float) = 5.0, min_voltage: (int, float) = 0.0,
                 mode: str = 'differential', timeout: (int, float) = None):
        self._device = device
        self._analog_input = analog_input
        self._sample_count, self._rate = sample_count, rate
        self._max_voltage, self._min_voltage = max_voltage, min_voltage
        self._mode, self._timeout = mode, timeout

    @property
    def value(self):
        """
        Return a single sample of the analog input

        :return: a floating-point value representing the voltage
        """
        return self.sample()

    def sample(self, analog_input: str = None):
        """
        Return a single sample of the analog input

        :return: a floating-point value representing the voltage
        """
        samples = _sample_analog_in(
            device=self._device,
            analog_input=analog_input if analog_input is not None else self._analog_input,
            sample_count=1,
            rate=self._rate,
            max_voltage=self._max_voltage,
            min_voltage=self._min_voltage,
            mode=self._mode, timeout=self._timeout
        )
        return samples[0]

    def capture(self, analog_input: str = None,
                sample_count: int = None,
                rate: (int, float) = None,
                max_voltage: (int, float) = None,
                min_voltage: (int, float) = None,
                mode: str = None,
                timeout: (int, float) = None):
        """
        Will capture <sample_count> samples at <rate>Hz in the <mode> mode.

        :param analog_input: the analog input name assigned by DAQmx (i.e. "ao0")
        :param sample_count: the number of samples to take
        :param rate: the frequency at which to sample the input
        :param max_voltage: the maximum expected voltage
        :param min_voltage: the minimum expected voltage
        :param mode: the mode; valid values: differential, pseudo-differential, /
            singled-ended referenced, singled-ended non-referenced
        :param timeout: the time at which an error will occur if no response /
            from the instrument is received.
        :return: a numpy array containing all resulting values
        """
        samples = _sample_analog_in(
            device=self._device,
            analog_input=analog_input if analog_input else self._analog_input,
            sample_count=sample_count if sample_count else self._sample_count,
            rate=rate if rate is not None else self._rate,
            max_voltage=max_voltage if max_voltage else self._max_voltage,
            min_voltage=min_voltage if min_voltage else self._min_voltage,
            mode=mode if mode else self._mode,
            timeout=timeout if timeout is not None else self._timeout
        )
        return samples

    def find_dominant_frequency(self, analog_input: str = None,
                                sample_count: int = None,
                                rate: (int, float) = None,
                                max_voltage: (int, float) = None,
                                min_voltage: (int, float) = None,
                                mode: str = None,
                                timeout: (int, float) = None):
        """
        Acquires the fundamental frequency observed within the samples

        :param analog_input: the NI analog input designation (i.e. 'ai0')
        :param sample_count: the number of samples to acquired
        :param rate: the sample rate in Hz
            :param max_voltage: the maximum voltage possible
        :param min_voltage: the minimum voltage range
        :param mode: the voltage mode of operation; choices: 'differential',
            'pseudo-differential', 'single-ended referenced',
            'single-ended non-referenced'
        :param timeout: the time at which the function should return if this
            time has elapsed; set to -1 to make infinite (default)
        :return: the frequency found to be at the highest amplitude; this is
            often the fundamental frequency in many domains
        """
        signal = self.capture(analog_input=analog_input if analog_input else self._analog_input,
                              sample_count=sample_count if sample_count else self._sample_count,
                              rate=rate if rate else None,
                              max_voltage=max_voltage if max_voltage is not None else self._max_voltage,
                              min_voltage=min_voltage if min_voltage is not None else self._min_voltage,
                              mode=mode if mode else self._mode,
                              timeout=timeout if timeout else self._timeout)

        fourier = np.fft.fft(signal)
        n = signal.size
        time_step = 1 / rate

        freq = np.fft.fftfreq(n, d=time_step)

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


class Port:
    """
    Represents the port object as defined by DAQmx.

    :param device: the device string as defined by DAQmx (i.e. 'Dev3')
    :param port: the port name as defined by DAQmx (i.e. 'port2')
    """
    def __init__(self, device: str, port: str):
        searcher = _NIDAQmxSearcher()

        self._device = device
        self._port = port

        lines = []
        for line in searcher.list_do_lines(device):
            _, p, l = line.split('/')
            if p == port:
                lines.append(l)
        self._lines = lines

    @property
    def lines(self):
        """
        Lists all of the lines attached to the port

        :return: a list of line names
        """
        return self._lines

    def __setattr__(self, key, value):
        if '_lines' in self.__dict__.keys():
            if key in self.__dict__['_lines']:
                if not isinstance(value, bool):
                    raise ValueError(f'{self._device}/{self._port}/{key} may only '
                                     f'be "True" or "False"')

                _digital_out_line(self._device, self._port, key, value)
            else:
                raise ValueError(f'line "{key}" does not exist on this port')
        else:
            self.__dict__[key] = value

    def __getattr__(self, item):
        if 'line' in item:
            value = _digital_in_line(self._device, self._port, item)
            return value


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
                 serial_number: (str, int) = None,
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
            if isinstance(serial_number, str):
                device = searcher.device_lookup_by_sn(int(serial_number, 16))
            else:
                device = searcher.device_lookup_by_sn(serial_number)
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

        # uses setattr to add attributes to a class at runtime
        analog_outputs = [ao.split('/')[1] for ao in searcher.list_ao(device)]
        digital_outputs = []
        for p in searcher.list_do_lines(device):
            _, p, _ = p.split('/')
            digital_outputs.append(p)
        digital_outputs = list(set(digital_outputs))

        self._outputs = analog_outputs + digital_outputs

        self._device = device
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(loglevel)

    def __setattr__(self, attr, value):
        if '_outputs' in self.__dict__.keys():
            if attr in ['_device', '_logger']:
                pass  # ignore the attributes that are
                      # supposed to be part of the class
            elif attr in self._outputs:
                if 'ao' in attr:
                    _analog_out(self._device, attr, value)
                else:
                    raise AttributeError(f'"{attr}" does not appear '
                                         f'to exist on the device')

        self.__dict__[attr] = value

    def __getattribute__(self, name):
        if 'port' in name:
            return Port(self._device, name)
        elif 'ai' == name:
            return AnalogInput(self._device, None)
        elif 'ai' in name:
            return AnalogInput(self._device, name)

        return super().__getattribute__(name)

    def __repr__(self):
        return f'<NIDAQmxInstrument Device:{self._device} ' \
               f'PN:{self.model} SN:{self.sn}>'

    @property
    def sn(self):
        """
        Returns the device serial number

        :return: the device serial number
        """
        return _NIDAQmxSearcher().product_serial_number(self._device)

    @property
    def model(self):
        """
        Returns the device model number

        :return: the device model number
        """
        return _NIDAQmxSearcher().model_number(self._device)

    @property
    def outputs(self):
        """
        Returns a list of outputs associated with the device.

        :return: a list of outputs associated with the device.
        """
        return self._outputs

    @property
    def inputs(self):
        """
        Returns a list of inputs associated with the device

        :return: a list of inputs associated with the device
        """
        searcher = _NIDAQmxSearcher()

        ais = searcher.list_ai(self._device)
        ais = [s.replace(f'{self._device}/', '') for s in ais]

        dis = searcher.list_do_lines(self._device)
        dis = [s.split('/')[1] for s in dis]

        return sorted(list(set(ais + dis)))


class _NIDAQmxSearcher:
    """
    This class is used to search the currently connected devices
    """
    STRING_BUF_LEN = 1000

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
        devices = [device for device in devices if device !='']

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
