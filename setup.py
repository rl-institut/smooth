from distutils.core import setup
from setuptools import find_packages

setup(
    name='smooth',
    version='0.2.0',
    packages=find_packages(),
    package_data={'smooth.examples': ['example_timeseries/*.csv']},
    license='Dual-License MIT/Apache-2.0',
    long_description=open('README.md').read(),
)
