#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
#
# copyright © 2018 Pete Alexandrou
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

import os
import sys

from PyQt5.QtCore import pyqtSignal, Qt, QDir, QFileInfo, QProcessEnvironment, QSettings, QTextStream
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import QApplication

import vidcutter


class SingleApplication(QApplication):
    messageReceived = pyqtSignal(str)

    def __init__(self, appid, *argv):
        super(SingleApplication, self).__init__(*argv)
        self._appid = appid
        self._activationWindow = None
        self._activateOnMessage = False
        self._outSocket = QLocalSocket()
        self._outSocket.connectToServer(self._appid)
        self._isRunning = self._outSocket.waitForConnected()
        self._outStream = None
        self._inSocket = None
        self._inStream = None
        self._server = None
        self.settings = QSettings(SingleApplication.getSettingsPath(), QSettings.IniFormat)
        self.singleInstance = self.settings.value('singleInstance', 'on', type=str) in {'on', 'true'}
        if self._isRunning and self.singleInstance:
            self._outStream = QTextStream(self._outSocket)
            for a in argv[0][1:]:
                a = os.path.join(os.getcwd(), a)
                if os.path.isfile(a):
                    self.sendMessage(a)
                    break
            sys.exit(0)
        else:
            error = self._outSocket.error()
            if error == QLocalSocket.ConnectionRefusedError:
                self.close()
                QLocalServer.removeServer(self._appid)
            self._outSocket = None
            self._server = QLocalServer()
            self._server.listen(self._appid)
            self._server.newConnection.connect(self._onNewConnection)

    def close(self):
        if self._inSocket:
            self._inSocket.disconnectFromServer()
        if self._outSocket:
            self._outSocket.disconnectFromServer()
        if self._server:
            self._server.close()

    @staticmethod
    def getSettingsPath() -> str:
        if sys.platform == 'win32':
            settings_path = os.path.join(QDir.homePath(), 'AppData', 'Local', 'vidcutter')
        elif sys.platform == 'darwin':
            settings_path = os.path.join(QDir.homePath(), 'Library', 'Preferences', 'vidcutter')
        else:
            if QFileInfo(__file__).absolutePath().startswith('/app/'):
                settings_path = QProcessEnvironment.systemEnvironment().value('XDG_CONFIG_HOME', '')
                if not len(settings_path):
                    settings_path = os.path.join(QDir.homePath(), '.var', 'app', vidcutter.__desktopid__, 'config')
            else:
                settings_path = os.path.join(QDir.homePath(), '.config', 'vidcutter')
        return os.path.join(settings_path, 'vidcutter.ini')

    def isRunning(self):
        return self._isRunning

    def appid(self):
        return self._appid

    def activationWindow(self):
        return self._activationWindow

    def setActivationWindow(self, activationWindow, activateOnMessage=True):
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    def activateWindow(self):
        if not self._activationWindow:
            return
        self._activationWindow.setWindowState(self._activationWindow.windowState() & ~Qt.WindowMinimized)
        self._activationWindow.raise_()
        self._activationWindow.activateWindow()

    def sendMessage(self, msg):
        if not self._outStream:
            return False
        # noinspection PyUnresolvedReferences
        self._outStream << msg << '\n'
        self._outStream.flush()
        return self._outSocket.waitForBytesWritten()

    def _onNewConnection(self):
        if self._inSocket:
            self._inSocket.readyRead.disconnect(self._onReadyRead)
        self._inSocket = self._server.nextPendingConnection()
        if not self._inSocket:
            return
        self._inStream = QTextStream(self._inSocket)
        self._inSocket.readyRead.connect(self._onReadyRead)
        if self._activateOnMessage:
            self.activateWindow()

    def _onReadyRead(self):
        while True:
            msg = self._inStream.readLine()
            if not msg:
                break
            self.messageReceived.emit(msg)
