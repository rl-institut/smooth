from distutils.core import setup
from setuptools import find_packages

setup(
    name='smooth',
    version='0.2.0',
    packages=find_packages(),
    package_data={'smooth.examples': ['example_timeseries/*.csv']},
    license='Dual-License MIT/Apache-2.0',
    long_description=open('README.md', encoding="utf-8").read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
