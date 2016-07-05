import logging
import traceback

import ping

def test_ping(config):
    log = logging.getLogger(__name__)
    address = config.get('ping.address')
    log.info('Trying to ping %s', address)
    try:
        lost, mrtt, artt = ping.quiet_ping(address)
    except Exception as e:
        log.error('Cannot ping: %s',
            traceback.format_exception_only(
                e.__class__.__name__, e))
        return None
    if lost != 0:
        log.error('Ping unsuccessful, mrtt=%.3f, artt=%.3f, lost=%.3f.',
            mrtt, artt, lost)
        return None
    log.info('Ping max: %.3fms, avg: %3fms.', mrtt, artt)
    return artt

