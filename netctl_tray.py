#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""Set an icon in the system tray indicating the netctl status"""

import sys
import os
import re
import subprocess

from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox, QMenu
import netctl_tray_rc


class NetworkInterface:
    """Interface to netctl"""

    def _get_raw_netctl_connections(self):
        return subprocess.check_output(["netctl", "list"]).decode().split('\n')[:-1]

    def get_active_connections(self):
        """Return a list of active, i.e. running, connections."""

        return [l[2:] for l in self._get_raw_netctl_connections() for m in [re.search(r'^\*', l)] if m]

    def get_quality(self):
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

    def default_interface(self):
        """Returns the interface of the default route."""

        interface = None
        stdout = subprocess.check_output(['ip', 'route', 'list', 'scope', 'global'])
        for line in stdout.decode().split('\n'):
            route = line.split(' ')
            if len(route) >= 5 and (route[0], route[1], route[3]) == ('default', 'via', 'dev'):
                interface = route[4]
                break
        return interface

    def carrier_ok(self, iface):
        """Check if the interface is connected."""

        iface_dir = '/sys/class/net/%s' % iface
        with open(iface_dir + '/carrier') as f:
            line = f.readline().strip()
            return line == '1'

    def interface_type(self, iface):
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


class SystemTrayIcon(QSystemTrayIcon):
    """A system tray icon displaying the network connection state."""

    def __init__(self, parent=None):
        icon = QIcon.fromTheme('network-wired-acquiring', QIcon(':wired-acquiring'))
        super(SystemTrayIcon, self).__init__(icon, parent)
        menu = QMenu(parent)
        # exit_action = menu.addAction("Exit")
        # exit_action.triggered.connect(QApplication.quit)
        self.setToolTip('Netctl')
        self.setContextMenu(menu)
        self.network_interface = NetworkInterface()

        self.update_loop()
        self.update_icon()

    @pyqtSlot()
    def update_loop(self):
        try:
            self.update_icon()
        finally:
            QTimer.singleShot(5000, self.update_loop)

    def update_icon(self):
        """Update the tray icon according to the type of connection."""

        default_interface = self.network_interface.default_interface()
        if self.network_interface.carrier_ok(default_interface):
            if self.network_interface.interface_type(default_interface) == 'wired':
                self.setIcon(QIcon.fromTheme('network-wired', QIcon(':wired')))
                self.setToolTip('Wired connection')
            else:
                quality = self.network_interface.get_quality()
                if quality >= 90:
                    self.setIcon(QIcon.fromTheme('network-wireless-excellent', QIcon(':excellent')))
                elif quality >= 70:
                    self.setIcon(QIcon.fromTheme('network-wireless-good', QIcon(':good')))
                elif quality >= 50:
                    self.setIcon(QIcon.fromTheme('network-wireless-ok', QIcon(':ok')))
                elif quality >= 30:
                    self.setIcon(QIcon.fromTheme('network-wireless-weak', QIcon(':weak')))
                elif quality >= 10:
                    self.setIcon(QIcon.fromTheme('network-wireless-none', QIcon(':none')))
                else:
                    self.setIcon(QIcon.fromTheme('network-wireless-disconnected', QIcon(':disconnected')))
                self.setToolTip('Wireless connection.\nSignal strength: {:.1f} %'.format(quality))
        else:
                self.setIcon(QIcon.fromTheme('network-wired-disconnected', QIcon(':disconnected')))
                self.setToolTip('No connection')


if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Systray",
                             "I couldn't detect any system tray on this system.")
        sys.exit(1)

    tray = SystemTrayIcon()
    tray.show()

    # set the exec loop going
    sys.exit(app.exec_())
