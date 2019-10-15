from distutils.core import setup

setup(
    name='smooth',
    version='0.1dev',
    packages=['smooth', 'smooth.components', 'smooth.examples', 'smooth.framework', 'smooth.optimization'],
    license='GNU AFFERO GENERAL PUBLIC LICENSE - Version 3, 19 November 2007',
    long_description=open('README.md').read(),
)