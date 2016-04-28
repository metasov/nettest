import socket
import time

def test_dns(config):
    domain = config.get('dns.domain')
    start_time = time.time()
    try:
        socket.gethostbyname(domain)
    except socket.error:
        return None
    stop_time = time.time()
    return stop_time - start_time

