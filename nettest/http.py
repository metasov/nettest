import time
import logging

from urllib3 import PoolManager, Timeout
from urllib3.exceptions import PoolError, HTTPError

from nettest.config import NettestConfig
from nettest.exceptions import ExecutionError

log = logging.getLogger(__name__)


def test_http(config):
    assert isinstance(config, NettestConfig)
    url = config.get('http.url')
    timeout = config.get('http.timeout', 10)
    chunk_size = config.get('http.chunk_size', 1024*1024)
    
    pool = PoolManager(timeout=float(timeout))
    
    start_time = time.time()

    log.info('Start fetching %s', url)

    try:
        result = pool.request('GET', url, assert_same_host=False)
    except (PoolError, HTTPError) as e:
        log.error(
            'Error while trying to fetch url %s',
            url, exc_info=1)
        raise ExecutionError('Cannot fetch url by HTTP')
    finally:
        stop_time = time.time()
        execution_time = stop_time - start_time
    
    total_bytes = len(result.data)

    speed = total_bytes / execution_time

    log.info(
        'Fetched %d bytes in %.3f seconds. '
        'Speed: %.3f Mbits/sec',
        total_bytes, execution_time, speed/(1024*1024))

    return speed

