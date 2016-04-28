import sys
import os
import logging

from nettest.exceptions import Error
from nettest.config import NettestConfig
from nettest.interface import test_interface
from nettest.http import test_http


log = logging.getLogger(__name__)

def run(config):
    try:
        release_time, acquire_time = test_interface(config)
    except Error as e:
        log.error('%s: %s', e.__class__.__name__, e)
        log.error('Error testing interface, cannot continue')
        return e.retval
    except Exception:
        log.exception('Error testing interface, cannot continue')
        raise
    
    try:
        http_speed = test_http(config)
    except Error as e:
        log.error(str(e))
        http_speed = None
    
    return 0


if __name__ == '__main__':
    try:
        config_name = sys.argv[1]
    except IndexError:
        sys.stderr.write('Please specify config file name\n')
        exit(998)

    config = NettestConfig()
    config.read(config_name)

    loglevel = logging.ERROR
    if os.environ.get('DEBUG', '0') == '1':
        loglevel = logging.INFO
    elif os.environ.get('DEBUG', '0') == '2':
        loglevel = logging.DEBUG

    logging.basicConfig(level=loglevel)
    
    exit(run(config))

