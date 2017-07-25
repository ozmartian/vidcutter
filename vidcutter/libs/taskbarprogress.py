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

import logging

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import qApp, QWidget

from PyQt5.QtDBus import QDBusConnection, QDBusMessage


class TaskbarProgress(QWidget):
    def __init__(self, parent=None):
        super(TaskbarProgress, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self._desktopFileName = '%s.desktop' % qApp.applicationName().lower()
        self._sessionbus = QDBusConnection.sessionBus()
        self.clear()

    @pyqtSlot()
    def clear(self):
        self.setProgress(0.0, False)

    @pyqtSlot(float, bool)
    def setProgress(self, value: float, visible: bool=True):
        self.logger.info('setprogress - value; %s    visible: %s' % (value, visible))
        signal = QDBusMessage.createSignal('/com/canonical/unity/launcherentry/337963624',
                                           'com.canonical.Unity.LauncherEntry', 'Update')
        message = signal << 'application://{0}'.format(self._desktopFileName) << {
            'progress-visible': visible,
            'progress': value
        }
        self._sessionbus.send(message)
