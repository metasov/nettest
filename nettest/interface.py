import sys
import logging
import time
import subprocess

from pyroute2 import IPDB, IPRoute

from nettest.config import NettestConfig
from nettest.exceptions import (InterfaceError,
                                ExecutionError,
                                TerminationError,
                                CannotAcquireIP)

log = logging.getLogger(__name__)

TIME_QUANTUM = 0.001


def test_interface(config):
    assert isinstance(config, NettestConfig)
    ifname = config.get('network.interface')
    dhclient = config.get('dhclient.binary')
    execution_timeout = config.getint('dhclient.execution_timeout')
    termination_timeout = config.getint('dhclient.termination_timeout')
    
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

    log.info('Obtaining IP address')

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

