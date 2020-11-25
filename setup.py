from setuptools import setup, find_packages
from ni import __version__

with open('requirements.txt', 'r') as f:
    REQUIREMENTS = [s.strip() for s in f.readlines()]

setup(
    name='ni',
    version=__version__,
    description='DAQ control using National Instruments DAQmx framework',
    author='Jason R. Jones',
    python_requires='>=3.6.0',
    install_requires=REQUIREMENTS,
    packages=find_packages(),
    license='',
    long_description='DAQ control using National Instruments DAQmx framework'
)
