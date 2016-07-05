import sys
import os
import logging
import logging.config

from nettest.exceptions import Error
from nettest.config import NettestConfig
from nettest.interface import test_interface
from nettest.http import test_http
from nettest.storage import NettestStorage
from nettest import ftp
from nettest.dns import test_dns
from nettest.nettest_ping import test_ping


def run(config):
    log = logging.getLogger(__name__)
    storage = NettestStorage(config)
    try:
        release_time, acquire_time = test_interface(config)
    except Error as e:
        log.error('%s: %s', e.__class__.__name__, e)
        log.error('Error testing interface, cannot continue')
        return e.retval
    except Exception:
        log.exception('Error testing interface, cannot continue')
        raise
    
    dns_time = test_dns(config)
    
    ping_rtt = test_ping(config)
    
    try:
        http_speeds = test_http(config)
    except Error as e:
        log.error(str(e))
        http_speeds = None
    
    try:
        ftp_download_speeds = ftp.test_download(config)
    except Error as e:
        log.error(str(e))
        ftp_download_speeds = None
    
    try:
        ftp_upload_speeds = ftp.test_upload(config)
    except Error as e:
        log.error(str(e))
        ftp_upload_speeds = None
    

    storage.update(acquire_time,
                   dns_time,
                   ping_rtt,
                   http_speeds,
                   ftp_download_speeds,
                   ftp_upload_speeds)
    
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

