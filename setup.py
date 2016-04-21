#/usr/bin/env python

from setuptools import setup

setup(
    name='nettest',
    version='0.0.2',
    description='Utility to measure network service SLA',
    author='Metasov Arthur',
    author_email='metasov@gmail.com',
    url='https://github.com/metasov/nettest',
    packages=['nettest'],
    install_requires=[
        'pyroute2 >= 0.3.21',
    ]
)

