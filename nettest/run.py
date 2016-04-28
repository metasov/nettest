import sys
import os
import logging
import logging.config

from nettest.exceptions import Error
from nettest.config import NettestConfig
from nettest.interface import test_interface
from nettest.http import test_http
from nettest import ftp


def run(config):
    log = logging.getLogger(__name__)
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
    
    try:
        ftp_download_speed = ftp.test_download(config)
    except Error as e:
        log.error(str(e))
        ftp_download_speed = None
    
    try:
        ftp_upload_speed = ftp.test_upload(config)
    except Error as e:
        log.error(str(e))
        ftp_upload_speed = None
    
    return 0


if __name__ == '__main__':
    try:
        config_name = sys.argv[1]
    except IndexError:
        sys.stderr.write('Please specify config file name\n')
        exit(998)

    config = NettestConfig()
    config.read(config_name)

    logging.config.fileConfig(config_name)
    
    exit(run(config))

