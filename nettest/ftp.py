import ftplib
import time
import logging
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from nettest.config import NettestConfig
from nettest.exceptions import ConfigReadError, ExecutionError

log = logging.getLogger(__name__)

K = 1024
M = K * K
G = M * M

class FtpDownloadStatistics(object):
    def __init__(self):
        self._total_bytes = 0
        self._start_time = time.time()
        self._last_time = self._start_time
        self._max_speed = None
        self._min_speed = None
        self._average_speed = None

    @property
    def average_speed(self):
        timedelta = self._last_time - self._start_time
        return self._total_bytes / timedelta

    @property
    def size(self):
        return self._total_bytes

    @property
    def max_speed(self):
        return self._max_speed

    @property
    def min_speed(self):
        return self._min_speed
    
    @property
    def time(self):
        return self._last_time - self._start_time

    def receive_chunk(self, data):
        if not data:
            return
        chunk_size = len(data)
        self._total_bytes += chunk_size
        new_time = time.time()
        timedelta = new_time - self._last_time
        self._last_time = new_time
        if timedelta != 0:
            chunk_speed = chunk_size / timedelta 

            if self._max_speed is None:
                self._max_speed = chunk_speed
            else:
                self._max_speed = max(self._max_speed, chunk_speed)

            if self._min_speed is None:
                self._min_speed = chunk_speed
            else:
                self._min_speed = min(self._min_speed, chunk_speed)

            log.debug(
                'Received %.1f Kb / %.2f Mb in %.2f sec. '
                'Speed: %.2f Mbit/s',
                float(chunk_size) / K,
                float(self._total_bytes) / M,
                timedelta,
                chunk_speed / M)


def test_upload(config):
    address = config.get('ftp.address')
    username = config.get('ftp.username', 'anonymous')
    password = config.get('ftp.password', 'anonymous@example.com')
    
    directory = config.get('ftp.upload_directory', '')
    filename = config.get('ftp.upload_filename')
    size = config.get('ftp.upload_size')

    chunk_size = config.get('ftp.chunk_size', 1024 * 1000)
    
    size = size.replace(' ', '').replace('\t', '')
    try:
        if size.endswith('G'):
            size = int(int(size[:-1]) * G)
        elif size.endswith('M'):
            size = int(int(size[:-1]) * M)
        elif size.endswith('K'):
            size = int(int(size[:-1]) * K)
        else:
            size = int(size)
    except (ValueError, TypeError):
        raise ConfigReadError(
            'ftp.upload_size should be integer optionally '
            'followed by K, M or G modificator. Found: %s', 
            repr(size))
    
    ftp = ftplib.FTP(address)
    ftp.login(username, password)
    
    if directory != '':
        ftp.cwd(directory)

    try:
        ftp.delete(filename)
    except ftplib.error_reply:
        # there is no such file
        pass
    except ftplib.error_perm:
        log.error(
            'Cannot delete existing file %s on FTP',
            filename)
    
    log.debug('Getting random data into memory')
    
    data = StringIO.StringIO()
    with open('/dev/urandom', 'r') as urandom:
        data.write(urandom.read(size))

    data.seek(0)

    log.debug('Starting FTP upload')

    start_time = time.time()
    ftp.storbinary('STOR ' + filename, data, chunk_size)
    stop_time = time.time()
    
    speed = size / (stop_time - start_time)
    
    log.debug('Done.')
    log.info('FTP upload speed: %.3f Mbit/s', speed / M)

    return speed

def test_download(config):
    address = config.get('ftp.address')
    username = config.get('ftp.username', 'anonymous')
    password = config.get('ftp.password', 'anonymous@example.com')

    directory = config.get('ftp.directory', '')
    filename = config.get('ftp.filename')
    
    chunk_size = config.get('ftp.chunk_size', 1024 * 1000)

    ftp = ftplib.FTP(address)
    ftp.login(username, password)

    if directory != '':
        ftp.cwd(directory)

    stats = FtpDownloadStatistics()

    ftp.retrbinary('RETR '+filename, stats.receive_chunk, chunk_size)

    log.info(
        'Received %.2f Mb in %d seconds. '
        'Average speed: %.3f Mbits/s. '
        'Max speed: %.3f Mbits/s. '
        'Min speed: %.3f Mbits/s. ',
        stats.size / M,
        stats.time,
        stats.average_speed / M,
        stats.max_speed / M,
        stats.min_speed / M
    )
    
    ftp.close()

    return stats.average_speed

