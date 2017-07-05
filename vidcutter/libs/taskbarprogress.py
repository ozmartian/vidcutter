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

import atexit
import sys

from PyQt5.QtCore import QDir, QFile, QFileInfo, QStandardPaths, QUuid
from PyQt5.QtDBus import QDBusConnection, QDBusMessage
from PyQt5.QtWidgets import qApp, QWidget


class TaskbarProgress(QWidget):
    def __init__(self, parent=None):
        super(TaskbarProgress, self).__init__(parent)
        atexit.register(self._doCleanup)
        self._desktopFile = QFile('{0}.desktop'.format(qApp.applicationName().lower()))
        self._desktopFileContent = '[Desktop Entry]\nType=Application\nVersion=1.1\nName=%s\nExec=%s\n'
        self._dbusMessage = QDBusMessage.createSignal('/com/ozmartians/VidCutter',
                                                      'com.canonical.Unity.LauncherEntry', 'Update')
        self._dbusConnection = QDBusConnection.sessionBus()

    def setProgress(self, value: float):
        self._sendMessage({
            'progress-visible': False if value <= 0 else True,
            'progress': value
        })

    def _createDesktopFile(self):
        name = '{0}.desktop'.format(QUuid.createUuid().toString())
        appsdir = QDir(QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation))
        self._desktopFile.setFileName(appsdir.absoluteFilePath(name))
        if not self._desktopFile.exists():
            content = self._desktopFileContent % (qApp.applicationName(), QFileInfo(sys.argv[0]).absoluteFilePath())
            self._desktopFile.open(QFile.WriteOnly)
            self._desktopFile.write(content.encode('utf-8'))
            self._desktopFile.close()
        self._reset()

    def _reset(self):
        self._sendMessage({
            'progress-visible': False,
            'progress': 0.0,
            'count-visible': False,
            'count': 0
        })

    # noinspection PyUnresolvedReferences
    def _sendMessage(self, params: dict):
        message = self._dbusMessage << 'application://{0}'.format(QFileInfo(self._desktopFile).fileName()) << params
        self._dbusConnection.send(message)

    def __del__(self):
        self._doCleanup()

    def _doCleanup(self):
        if hasattr(self, '_desktopFile'):
            if self._desktopFile.exists():
                self._desktopFile.remove()
