import sys
import logging
import time
import subprocess

from pyroute2 import IPDB, IPRoute
from ConfigParser import (SafeConfigParser,
                          NoSectionError,
                          NoOptionError)

from nettest.exceptions import (
    Error,
    ConfigReadError,
    InterfaceError,
    ExecutionError,
    TerminationError,
    CannotAcquireIP
)

log = logging.getLogger(__name__)

TIME_QUANTUM = 0.001

def get_config(filename):
    config = SafeConfigParser()
    config.read(filename)
    return config

def main(config_name):
    config = get_config(config_name)
    try:
        ifname = config.get('network', 'interface')
    except (NoSectionError, NoOptionError) as e:
        raise ConfigReadError(
            'Error while getting network.interface from config')
    
    try:
        dhclient = config.get('dhclient', 'binary')
    except (NoSectionError, NoOptionError) as e:
        raise ConfigReadError(
            'Error while getting dhclient.binary from config')
    
    try:
        execution_timeout = config.getint('dhclient', 'execution_timeout')
    except ValueError:
        raise ConfigReadError(
            'dhclient.execution_timeout should be integer')
    except (NoSectionError, NoOptionError):
        raise ConfigReadError(
            'Error while getting dhclient.execution_timeout from config')
    
    try:
        termination_timeout = config.getint(
            'dhclient', 'termination_timeout')
    except ValueError:
        raise ConfigReadError(
            'dhclient.termination_timeout should be integer')
    except (NoSectionError, NoOptionError):
        raise ConfigReadError(
            'Error while getting dhclient.termination_timeout from config')
    
    ipdb = IPDB(mode='implicit')
    ip = IPRoute()

    if ifname not in ipdb.interfaces:
        raise InterfaceError('Interface %s cannot be found' % ifname)

    interface = ipdb.interfaces.get(ifname)

    log.info('Releasing IP address and stopping dhclient')
    
    start_time = time.time()
   
    try:
        release_process = subprocess.Popen(
            [dhclient, '-r', '-v', ifname],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    except OSError as e:
        log.exception()
        raise ExecutionError('Cannot execute %s' % dhclient)

    while release_process.poll() is None:
        time.sleep(TIME_QUANTUM)
        if time.time() - start_time > execution_timeout:
            log.error(
                'Timeout exceeded waiting for dhclient to release ip')
            release_process.terminate()
            time.sleep(termination_timeout)
            if relase_process.poll() is None:
                release_process.kill()
                if release_process.poll() is None:
                    raise TerminationError(
                        'Cannot kill hanged dhclient process, exiting')
    
    release_time_used = time.time() - start_time
    del start_time
    
    if release_process.poll() != 0:
        stdout, stderr = release_process.communicate()
        log.error(
            'Dhclient cannot release IP address. Output was: %s %s',
            stdout, stderr)
    del release_process
    
    log.info(
        'Time used to release IP adderess: %.2f ms',
        release_time_used*1000)

    log.info('Deleting any left ip addresses')
    if interface.ipaddr:
        for ipaddr, prefixlen in interface.ipaddr:
            interface.del_ip(ipaddr, prefixlen)
        interface.commit()
    
    log.info('Shutting down %s', ifname)
    interface.down().commit()
    
    start_time = time.time()

    log.info('Bringing %s up', ifname)
    interface.up().commit()

    try:
        acquire_process = subprocess.Popen(
            [dhclient, '-1', '-4', '-v', ifname],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    except OSError as e:
        log.exception()
        raise ExecutionError('Cannot execute %s' % dhclient)

    while acquire_process.poll() is None:
        time.sleep(TIME_QUANTUM)
        if time.time() - start_time > execution_timeout:
            log.error(
                'Timeout exceeded waiting for dhclient to acquire ip')
            acquire_process.terminate()
            time.sleep(termination_timeout)
            if acquire_process.poll() is None:
                acquire_process.kill()
                if acquire_process.poll() is None:
                    raise TerminationError(
                        'Cannot kill hanged dhclient process, exiting')
            raise CannotAcquireIP('Dhclient timeout exceeded')
    
    acquire_time_used = time.time() - start_time
    del start_time

    if acquire_process.poll() != 0:
        stdout, stderr = acquire_process.communicate()
        raise CannotAcquireIP(
            'Dhclient cannot acquire IP address. Output was: %s %s',
            stdout, stderr)

    log.info(
        'Time used to up interface and acquire '
        'ip address: %.2f ms', acquire_time_used * 1000)

    return release_time_used, acquire_time_used

if __name__ == '__main__':
    import sys
    try:
        config_name = sys.argv[1]
    except IndexError:
        sys.stderr.write('Please specify config file name\n')
        exit(998)

    logging.basicConfig(level=logging.INFO)
    try:
        release_time, acquire_time = main(config_name)
    except Error as e:
        log.critical(str(e))
        exit(e.retval)
    except Exception:
        log.exception('Unhandled exception in main()')
        exit(999)
    exit(0)

