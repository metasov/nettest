import ftplib
import time
import logging
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from nettest.config import NettestConfig
from nettest.exceptions import ConfigReadError, ExecutionError

K = 1024
M = K * K
G = M * M


class FtpStatistics(object):
    def __init__(self):
        self._log = logging.getLogger(
            '.'.join([__name__, self.__class__.__name__]))
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

    def process_chunk(self, data):
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

            self._log.debug(
                'Processed %.1f Kb / %.2f Mb in %.2f sec. '
                'Speed: %.2f Mbit/s',
                float(chunk_size) / K,
                float(self._total_bytes) / M,
                timedelta,
                chunk_speed / M)


def _test_upload(address, username, password,
                 directory, filename, size,
                 chunk_size, timeout):
    log = logging.getLogger(__name__)
    
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
            'ftp upload_size should be integer optionally '
            'followed by K, M or G modificator. Found: %s', 
            repr(size))
    
    try:
        ftp = ftplib.FTP(address, username, password, '', timeout)
    except IOError as e:
        raise ExecutionError(
            'IOError while connecting to FTP: %s' % e)
    
    if directory != '':
        ftp.cwd(directory)

    try:
        ftp.delete(filename)
    except ftplib.error_reply:
        # there is no such file
        pass
    except ftplib.error_perm:
        log.info(
            'Cannot delete existing file %s on FTP',
            filename)
    
    log.debug('Getting random data into memory')
    
    data = StringIO.StringIO()
    with open('/dev/urandom', 'r') as urandom:
        data.write(urandom.read(size))

    data.seek(0)

    stats = FtpStatistics()

    log.debug('Starting FTP upload')

    try:
        ftp.storbinary('STOR ' + filename,
                       data,
                       chunk_size,
                       stats.process_chunk)
    except IOError as e:
        raise ExecutionError(
            'IOError while uploading file to FTP: %s' % e)
    
    log.debug('Done.')
    log.info(
        'Sent %.2f Mb in %.2f seconds. '
        'Average speed: %.3f Mbits/s. '
        'Max speed: %.3f Mbits/s. '
        'Min speed: %.3f Mbits/s. ',
        stats.size / M,
        stats.time,
        stats.average_speed / M,
        stats.max_speed / M,
        stats.min_speed / M
    )
    return stats.average_speed

def test_upload(config):
    speeds = []
    for key in config.get('ftp.keys').split(','):
        key = key.strip()
        address = config.get('ftp_%s.address' % key)
        username = config.get('ftp_%s.username' % key,
                              'anonymous')
        password = config.get('ftp_%s.password' % key,
                              'anonymous@example.com')
        
        directory = config.get('ftp_%s.upload_directory' % key,
                               '')
        filename = config.get('ftp_%s.upload_filename' % key)
        size = config.get('ftp_%s.upload_size' % key)

        chunk_size = config.get('ftp_%s.chunk_size' % key,
                                1024 * 1000)
        timeout = config.get('ftp_%s.timeout' % key, 30)
        
        speeds.append(
            _test_upload(
                address, username, password, directory,
                filename, size, chunk_size, timeout))
    
    return tuple(speeds)

def _test_download(address, username, password,
                   directory, filename, chunk_size,
                   timeout):
    log = logging.getLogger(__name__)

    try:
        ftp = ftplib.FTP(address, username, password, '', timeout)
    except IOError as e:
        raise ExecutionError(
            'IOError while connecting to FTP: %s' % e)

    if directory != '':
        ftp.cwd(directory)

    stats = FtpStatistics()
    
    try:
        ftp.retrbinary('RETR '+filename,
                       stats.process_chunk,
                       chunk_size)
    except IOError as e:
        raise ExecutionError(
            'IOError while downloading from FTP: %s' % e) 

    log.info(
        'Received %.2f Mb in %.2f seconds. '
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

def test_download(config):
    speeds = []
    for key in config.get('ftp.keys').split(','):
        key = key.strip()
        address = config.get('ftp_%s.address' % key)
        username = config.get('ftp_%s.username' % key,
                              'anonymous')
        password = config.get('ftp_%s.password' % key,
                              'anonymous@example.com')

        directory = config.get('ftp_%s.directory' % key, '')
        filename = config.get('ftp_%s.filename' % key)
        
        chunk_size = config.get('ftp_%s.chunk_size' % key,
                                1024 * 1000)
        timeout = config.get('ftp_%s.timeout' % key, 30)

        speeds.append(
            _test_download(
                address, username, password,
                directory, filename, chunk_size, timeout))
    return tuple(speeds)

