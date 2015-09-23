#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""Set an icon in the system tray indicating the netctl status"""

import sys

from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox, QMenu

import network_interface


class SystemTrayIcon(QSystemTrayIcon):
    """A system tray icon displaying the network connection state."""

    def __init__(self, parent=None):
        icon = QIcon.fromTheme('network-wired-acquiring', QIcon(':wired-acquiring'))
        super(SystemTrayIcon, self).__init__(icon, parent)
        menu = QMenu(parent)
        self.setToolTip('Netctl')
        self.setContextMenu(menu)

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

        default_interface = network_interface.default_interface()
        if network_interface.carrier_ok(default_interface):
            if network_interface.interface_type(default_interface) == 'wired':
                self.setIcon(QIcon.fromTheme('network-wired', QIcon(':wired')))
                self.setToolTip('Wired connection')
            else:
                quality = network_interface.get_quality()
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
    app.setApplicationName('Netctl tray')

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Systray",
                             "I couldn't detect any system tray on this system.")
        sys.exit(1)

    tray = SystemTrayIcon()
    tray.show()

    # set the exec loop going
    sys.exit(app.exec_())
