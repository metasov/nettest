import time
import logging

import urllib2

from nettest.config import NettestConfig
from nettest.exceptions import ExecutionError


K = 1024
M = K * K


def _test(url, timeout, chunk_size): 
    log = logging.getLogger(__name__)
    
    start_time = time.time()

    log.info('Start fetching %s', url)

    try:
        req = urllib2.urlopen(url, timeout=float(timeout))
    except (urllib2.URLError, urllib2.HTTPError) as e:
        log.error(
            'Error while trying to connect to url %s: %s',
            url, e)
        raise ExecutionError('Cannot fetch url by HTTP')
    
    total_bytes = 0
    avg_speed = 0
    min_speed = None
    max_speed = None
    while True:
        chunk_start_time = time.time()
        try:
            data = req.read(chunk_size)
        except IOError as e:
            raise ExecutionError(
                'IOError while reading file by HTTP: %s' % e)
        chunk_stop_time = time.time()
        
        execution_time = chunk_stop_time - start_time
        chunk_execution_time = chunk_stop_time - chunk_start_time
       
        chunk_size = len(data)
        total_bytes += chunk_size
        
        del data
        
        if chunk_size == 0:
            break

        speed = chunk_size / chunk_execution_time
        avg_speed = total_bytes / execution_time

        if min_speed is None:
            min_speed = speed
        elif speed > 0:
            min_speed = min(min_speed, speed)
        
        if max_speed is None:
            max_speed = speed
        elif speed > 0:
            max_speed = max(max_speed, speed)

        log.debug(
            'Read %.1f Kb / %.2f Mb. '
            'Speed: %.2f Mb/s. '
            'Avg speed %.2f Mb/s',
            float(chunk_size) / K,
            float(total_bytes) / M,
            speed / M,
            avg_speed / M)
    
    stop_time = time.time()
    execution_time = stop_time - start_time

    log.info('Fetched %d bytes in %.3f seconds. ',
             total_bytes, execution_time)

    log.info('Average speed: %.3f Mbit/s. '
             'Min speed: %.3f Mbit/s '
             'Max speed: %.3f. Mbit/s',
             avg_speed / M,
             min_speed / M,
             max_speed / M)

    return avg_speed


def test_http(config): 
    assert isinstance(config, NettestConfig)
    http_keys = config.get('http.keys')
    speeds = []
    for key in http_keys.split(','):
        key = key.strip()
        timeout = config.get('http_%s.timeout' % key, 10)
        chunk_size = config.get(
            'http_%s.chunk_size' % key, 1024*1000)
        url = config.get('http_%s.url' % key)
        
        speeds.append(_test(url, timeout, chunk_size))
    return tuple(speeds)

