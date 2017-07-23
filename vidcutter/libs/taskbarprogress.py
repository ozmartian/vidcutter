#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
#
# copyright © 2017 Pete Alexandrou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import qApp, QWidget

if sys.platform == 'win32':
    # noinspection PyUnresolvedReferences
    from PyQt5.QtWinExtras import QWinTaskbarButton
elif sys.platform.startswith('linux'):
    from PyQt5.QtDBus import QDBusConnection, QDBusMessage


class TaskbarProgress(QWidget):
    def __init__(self, parent=None):
        super(TaskbarProgress, self).__init__(parent)
        self.parent = parent
        if sys.platform == 'win32':
            self.taskbarButton = QWinTaskbarButton(self)
            self.taskbarButton.setWindow(self.parent.parent.windowHandle())
            self.taskbarProgress = self.taskbarButton.progress()
            self.taskbarProgress.setRange(0, 100)
        elif sys.platform.startswith('linux'):
            self._desktopFileName = '%s.desktop' % qApp.applicationName().lower()
            self._signal = QDBusMessage.createSignal('/com/canonical/unity/launcherentry/337963624',
                                                     'com.canonical.Unity.LauncherEntry', 'Update')
            self._sessionbus = QDBusConnection.sessionBus()

    @pyqtSlot()
    def clear(self):
        self.setProgress(0.0, False)

    @pyqtSlot(float)
    def setProgress(self, value: float, visible: bool=True):
        if sys.platform == 'win32':
            self.taskbarProgress.setVisible(True if value > 0.0 else False)
            self.taskbarProgress.setValue(value * 100)
        elif sys.platform.startswith('linux'):
            message = self._signal << 'application://{0}'.format(self._desktopFileName) << {
                'progress-visible': visible,
                'progress': value
            }
            self._sessionbus.send(message)
