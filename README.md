# Tool to test networking SLA

This tool tests time needed to bring ehternet interface
up and get IP address by dhcp

Requirements:
* python2
* pyroute2
* dhclient

Installation:
    python setup.py install

Usage:
    python -m nettest.run path/to/config.ini
