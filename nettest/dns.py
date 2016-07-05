import logging
import socket
import time

def test_dns(config):
    log = logging.getLogger(__name__)
    domain = config.get('dns.domain')
    log.info('Trying to resolve dns name %s', domain)
    start_time = time.time()
    try:
        socket.gethostbyname(domain)
    except socket.error as e:
        log.error(
            'Cannot resolve name: %s',
            traceback.format_exception_only(
                e.__class__.__name__, e))
        return None
    stop_time = time.time()
    log.info('Time: %.3f sec.', stop_time - start_time)
    return stop_time - start_time

