from distutils.core import setup
from setuptools import find_packages

setup(
    name='smooth',
    version='0.2.0',
    packages=find_packages(),
    package_data={'smooth.examples': ['example_timeseries/*.csv']},
    license='GNU AFFERO GENERAL PUBLIC LICENSE - Version 3, 19 November 2007',
    long_description=open('README.md').read(),
    #install_requires=[
        #'oemof@git+git://github.com/oemof/oemof-solph@585b123e3dc02b191fead4d202ba60c057c473fd',
        #'matplotlib',
        #'pandas<0.26',
        #'numpy<1.18',
        #'scipy',
        #'dill',
        #'pyutilib==5.8.0',
    #]
)
