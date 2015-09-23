# -*- coding: utf-8 -*-
"""Interface to netctl"""

import os
import re
import subprocess


def _get_raw_netctl_connections():
    return subprocess.check_output(["netctl", "list"]).decode().split('\n')[:-1]


def get_active_connections():
    """Return a list of active, i.e. running, connections."""

    return [l[2:] for l in _get_raw_netctl_connections() for m in [re.search(r'^\*', l)] if m]


def get_quality():
    """Return the wifi connection quality as a percentage."""

    stdout = subprocess.check_output(['iwconfig'], stderr=open(os.devnull, 'wb'))
    quality = ''
    for line in stdout.decode().split('\n'):
        if 'Quality' in line:
            quality = line
            break
    q_max = int(quality[26:28])
    q = int(quality[23:25])
    return 1. * q / q_max * 100


def default_interface():
    """Returns the interface of the default route."""

    interface = None
    stdout = subprocess.check_output(['ip', 'route', 'list', 'scope', 'global'])
    for line in stdout.decode().split('\n'):
        route = line.split(' ')
        if len(route) >= 5 and (route[0], route[1], route[3]) == ('default', 'via', 'dev'):
            interface = route[4]
            break
    return interface


def carrier_ok(iface):
    """Check if the interface is connected."""

    iface_dir = '/sys/class/net/%s' % iface
    with open(iface_dir + '/carrier') as f:
        line = f.readline().strip()
        return line == '1'


def interface_type(iface):
    """http://stackoverflow.com/questions/4475420/detect-network-connection-type-in-linux/16060638#16060638)"""

    res = 'wired'
    iface_dir = '/sys/class/net/%s' % iface
    with open(iface_dir + '/type') as f:
        line = f.readline().strip()
        if line == '1':
            res = 'wired'
            if 'wireless' in os.listdir(iface_dir) or 'phy80211' in os.listdir(iface_dir):
                res = 'wireless'
    return res
