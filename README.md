# Tool to test networking SLA

This tool tests time needed to bring ehternet interface
up and get IP address by dhcp

Requirements:
* python2
* pyroute2
* emails (needs lxml)
* dhclient in system

Installation:
```python setup.py install```

Usage:
To run test and save data:
    ```python -m nettest.run path/to/config.ini```

To send report via email:
    ```python -m nettest.report path/to/config.ini```
