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

import os
import time

from PyQt5.QtCore import pyqtSlot, Qt, QFileInfo, QTimer, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import qApp, QDialog, QPushButton


class Notification(QDialog):
    duration = 10

    def __init__(self, parent=None, f=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint):
        super(Notification, self).__init__(parent, f)
        self.parent = parent
        self.theme = self.parent.theme
        self.setStyleSheet('QDialog { border: 1px solid #999; }')
        self.setWindowModality(Qt.NonModal)
        self.setWindowOpacity(0.0)
        self._title, self._message = '', ''
        self._icons = dict()
        self._buttons = list()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def message(self):
        return self._message
    
    @message.setter
    def message(self, value):
        self._message = value

    @property
    def icons(self):
        return self._icons

    @icons.setter
    def icons(self, value):
        self._icons = value

    @property
    def buttons(self):
        return self._buttons

    @buttons.setter
    def buttons(self, value):
        self._buttons = value

    def mousePressEvent(self, event):
        self.close()

    # noinspection PyTypeChecker
    def showEvent(self, event):
        for step in range(0, 100, 5):
            self.setWindowOpacity(step / 100)
            qApp.processEvents()
            time.sleep(0.05)
        self.deleteLater()
        QTimer.singleShot(self.duration * 1000, self.close)
        super(Notification, self).showEvent(event)

    def closeEvent(self, event):
        for step in range(100, 0, -5):
            self.setWindowOpacity(step / 100)
            qApp.processEvents()
            time.sleep(0.05)
        self.deleteLater()
        super(Notification, self).closeEvent(event)


class JobCompleteNotification(Notification):
    def __init__(self, parent=None):
        super(JobCompleteNotification, self).__init__(parent)
        self.setObjectName('genericdialog3')
        # self.setIconPixmap(self.parent.thumbsupIcon.pixmap(150, 144))
        pencolor = '#C681D5' if self.theme == 'dark' else '#642C68'
        self.title = 'Your new media file is ready!'
        self.message = '''
    <style>
        h1 {
            color: %s;
            font-family: "Futura LT", sans-serif;
            font-weight: 400;
            text-align: center;
        }
        table.info {
            margin: 6px;
            padding: 4px 2px;
        }
        td.value {
            font-size: 13px;
            color: %s;
        }
        td.label {
            font-size: 12px;
            color: %s;
            padding-top: 5px;
            text-transform: lowercase;
            text-align: right;
            padding-right: 5px;
        }
    </style>
    <table class="info" cellpadding="2" cellspacing="0" align="left" width="350">
        <tr>
            <td width="20%%" class="label"><b>File:</b></td>
            <td width="80%%" class="value" nowrap>%s</td>
        </tr>
        <tr>
            <td width="20%%" class="label"><b>Size:</b></td>
            <td width="80%%" class="value">%s</td>
        </tr>
        <tr>
            <td width="20%%" class="label"><b>Length:</b></td>
            <td width="80%%" class="value">%s</td>
        </tr>
    </table>''' % (pencolor, ('#EFF0F1' if self.theme == 'dark' else '#222'),
                        pencolor, os.path.basename(self.parent.finalFilename),
                        self.parent.sizeof_fmt(int(QFileInfo(self.parent.finalFilename).size())),
                        self.parent.delta2QTime(self.parent.totalRuntime).toString(self.parent.runtimeformat))
        self.icons = {
            'play': QIcon(':/images/%s/complete-play.png' % self.theme)
        }
        playButton = QPushButton(self.icons['play'], 'Play', self)
        playButton.clicked.connect(self.playMedia)
        self.buttons.append(playButton)

    @pyqtSlot()
    def playMedia(self) -> None:
        if len(self.parent.finalFilename) and os.path.exists(self.parent.finalFilename):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.parent.finalFilename))

    # self.btn_open = self.addButton('Open', self.ResetRole)
    # self.btn_open.setIcon(self.icon_open)
    # self.btn_open.clicked.connect(lambda: self.playMedia(True))
    # btn_restart = self.addButton('Restart', self.AcceptRole)
    # btn_restart.setIcon(self.icon_restart)
    # btn_restart.clicked.connect(self.parent.parent.reboot)
    # self.btn_play = self.addButton('Play', self.ResetRole)
    # self.btn_play.setIcon(self.icon_play)
    # self.btn_play.clicked.connect(self.playMedia)
    # self.btn_exit = self.addButton('Exit', self.ResetRole)
    # self.btn_exit.setIcon(self.icon_exit)
    # self.btn_exit.clicked.connect(self.parent.close)
    # btn_continue = self.addButton('Continue', self.AcceptRole)
    # btn_continue.setIcon(self.icon_continue)
    # btn_continue.clicked.connect(self.close)

# def initIcons(self) -> None:
    # self.icon_exit = QIcon(':/images/%s/complete-exit.png' % self.theme)
    # self.icon_open = QIcon(':/images/%s/complete-open.png' % self.theme)
    # self.icon_restart = QIcon(':/images/%s/complete-restart.png' % self.theme)
    # self.icon_continue = QIcon(':/images/%s/complete-continue.png' % self.theme)
