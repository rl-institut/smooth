from distutils.core import setup
from setuptools import find_packages#,setup

setup(
    name='smooth',
    version='0.1dev',
    packages = find_packages(),
    package_data={'smooth.examples': ['example_timeseries/*.csv']},
    license='GNU AFFERO GENERAL PUBLIC LICENSE - Version 3, 19 November 2007',
    long_description=open('README.md').read(),
)
