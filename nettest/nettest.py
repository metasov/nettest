import sys
import logging
import time
import subprocess

from pyroute2 import IPDB, IPRoute
from ConfigParser import (SafeConfigParser,
                          NoSectionError,
                          NoOptionError)

log = logging.getLogger(__name__)

TIME_QUANTUM = 0.001
CONFIG_READ_ERROR = 1
INTERFACE_NOT_FOUND = 2
EXECUTION_ERROR = 3
TERMINATION_ERROR = 4
CANNOT_ACQUIRE_IP = 5


def get_config(filename):
    config = SafeConfigParser()
    config.read(filename)
    return config

def main():
    logging.basicConfig(level=logging.INFO)
    config = get_config('config.ini')
    try:
        ifname = config.get('network', 'interface')
    except (NoSectionError, NoOptionError) as e:
        log.critical('Error while getting network.interface from config')
        return CONFIG_READ_ERROR
    
    try:
        dhclient = config.get('dhclient', 'binary')
    except (NoSectionError, NoOptionError) as e:
        log.critical('Error while getting dhclient.binary from config')
        return CONFIG_READ_ERROR
    
    try:
        execution_timeout = config.getint('dhclient', 'execution_timeout')
    except ValueError:
        log.critical('dhclient.execution_timeout should be integer')
    except (NoSectionError, NoOptionError):
        log.critical(
            'Error while getting dhclient.execution_timeout from config')
        return CONFIG_READ_ERROR
    
    try:
        termination_timeout = config.getint(
            'dhclient', 'termination_timeout')
    except ValueError:
        log.critical('dhclient.termination_timeout should be integer')
    except (NoSectionError, NoOptionError):
        log.critical(
            'Error while getting dhclient.termination_timeout from config')
        return CONFIG_READ_ERROR
    
    ipdb = IPDB(mode='implicit')
    ip = IPRoute()

    if ifname not in ipdb.interfaces:
        log.critical('Interface %s cannot be found', ifname)
        return INTERFACE_NOT_FOUND

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
        log.critical(
            'Cannot execute %s',
            dhclient,
            exc_info=1)
        return EXECUTION_ERROR

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
                    log.critical(
                        'Cannot kill hanged dhclient process, exiting')
                    return TERMINATION_ERROR
    
    time_used = time.time() - start_time
    del start_time
    
    if release_process.poll() != 0:
        stdout, stderr = release_process.communicate()
        log.error(
            'Dhclient cannot release IP address. Output was: %s %s',
            stdout, stderr)
    del release_process
    
    log.info('Time used to release IP adderess: %.2f ms', time_used*1000)
    del time_used

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
        log.critical(
            'Cannot execute %s',
            dhclient,
            exc_info=1)
        return EXECUTION_ERROR

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
                    log.critical(
                        'Cannot kill hanged dhclient process, exiting')
                    return TERMINATION_ERROR
            return CANNOT_ACQUIRE_IP
    
    time_used = time.time() - start_time
    del start_time

    if acquire_process.poll() != 0:
        stdout, stderr = acquire_process.communicate()
        log.error(
            'Dhclient cannot acquire IP address. Output was: %s %s',
            stdout, stderr)
        return CANNOT_ACQUIRE_IP

    log.info(
        'Time used to up interface and acquire '
        'ip address: %.2f ms', time_used * 1000)

    return 0

if __name__ == '__main__':
    retno = main() or 0
    exit(retno)
