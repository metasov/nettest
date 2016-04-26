import sys
import logging

from ConfigParser import SafeConfigParser
from nettest.interface import test_interface
from nettest.exceptions import (
    Error,
    ConfigReadError,
    InterfaceError,
    ExecutionError,
    TerminationError,
    CannotAcquireIP
)


log = logging.getLogger(__name__)

def run(config):
    try:
        release_time, acquire_time = test_interface(config)
    except Error as e:
        log.critical(str(e))
        return e.retval
    except Exception:
        log.exception('Unhandled exception in test_interface()')
        return 999

if __name__ == '__main__':
    try:
        config_name = sys.argv[1]
    except IndexError:
        sys.stderr.write('Please specify config file name\n')
        exit(998)

    config = SafeConfigParser()
    config.read(config_name)

    logging.basicConfig(level=logging.INFO)
    
    exit(run(config))

