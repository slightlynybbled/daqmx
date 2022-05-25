from setuptools import setup, find_packages
from daqmx import __version__

with open('requirements.txt', 'r') as f:
    REQUIREMENTS = [s.strip() for s in f.readlines()]

with open('readme.md', 'r') as f:
    README = f.read()

setup(
    name='daqmx',
    version=__version__,
    description='DAQ control using National Instruments DAQmx framework',
    author='Jason R. Jones',
    author_email='slightlynybbled@gmail.com',
    url='https://github.com/slightlynybbled/daqmx',
    python_requires='>=3.6.0',
    install_requires=REQUIREMENTS,
    packages=find_packages(),
    zip_safe=True,
    license='MIT',
    long_description=README,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Natural Language :: English'
    ],
    keywords=['nationalinstruments', 'national', 'instruments',
             'national instruments', 'daqmx', 'nidaqmx', 'daq',
              'data acquisition', 'usb-6001']
)
