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
from PyQt5.QtGui import QDesktopServices, QIcon, QPixmap
from PyQt5.QtWidgets import qApp, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class Notification(QDialog):
    duration = 10

    def __init__(self, parent=None, f=Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint):
        super(Notification, self).__init__(parent, f)
        self.parent = parent
        self.theme = self.parent.theme
        self.setObjectName('notification')
        self.setMinimumWidth(450)
        self._title, self._message = '', ''
        self._icons = dict()
        self.buttons = list()
        self.msgLabel = QLabel(self)
        self.msgLabel.setWordWrap(True)
        logo = QPixmap(82, 82)
        logo.load(':/images/vidcutter-small.png', 'PNG')
        logo_label = QLabel(self)
        logo_label.setPixmap(logo)
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(logo_label)
        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.msgLabel)
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addLayout(self.left_layout)
        layout.addSpacing(10)
        layout.addLayout(self.right_layout)
        layout.addStretch(1)
        self.setLayout(layout)

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

    def mousePressEvent(self, event):
        self.close()

    # noinspection PyTypeChecker
    def showEvent(self, event):
        self.msgLabel.setText(self._message)
        [self.left_layout.addWidget(btn) for btn in self.buttons]
        screen = qApp.desktop().screenNumber(self.parent)
        bottomright = qApp.screens()[screen].availableGeometry().bottomRight()
        self.setGeometry(bottomright.x() - (459 + 5), bottomright.y() - (156 + 10), 459, 156)
        QTimer.singleShot(self.duration * 1000, self.close)
        super(Notification, self).showEvent(event)

    def closeEvent(self, event):
        for step in range(100, 0, -10):
            self.setWindowOpacity(step / 100)
            qApp.processEvents()
            time.sleep(0.2)
        self.done(0)
        super(Notification, self).closeEvent(event)


class JobCompleteNotification(Notification):
    def __init__(self, parent=None):
        super(JobCompleteNotification, self).__init__(parent)
        # self.setIconPixmap(self.parent.thumbsupIcon.pixmap(150, 144))
        pencolor = '#C681D5' if self.theme == 'dark' else '#642C68'
        self.title = 'Your media file is ready!'
        self.message = '''
    <style>
        h2 {
            color: %s;
            font-family: "Futura LT", sans-serif;
            font-weight: 500;
            text-align: center;
        }
        table.info {
            margin: 6px;
            padding: 4px 2px;
        }
        td.label {
            font-size: 11px;
            color: %s;
            padding-top: 5px;
            text-transform: lowercase;
            text-align: right;
            padding-right: 5px;
            font-family: "Futura LT", sans-serif;
        }
        td.value {
            font-size: 13px;
            color: %s;
        }
    </style>
    <div style="margin:20px 10px 0;">
        <h2>%s</h2>
        <table class="info" cellpadding="2" cellspacing="0" align="left" width="315">
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
        </table>
    </div>''' % (pencolor, pencolor, ('#EFF0F1' if self.theme == 'dark' else '#222'), self._title,
                 os.path.basename(self.parent.finalFilename),
                 self.parent.sizeof_fmt(int(QFileInfo(self.parent.finalFilename).size())),
                 self.parent.delta2QTime(self.parent.totalRuntime).toString(self.parent.runtimeformat))
        self.icons = {
            'play': QIcon(':/images/%s/complete-play.png' % self.theme)
        }
        playButton = QPushButton(self.icons['play'], 'Play', self)
        playButton.setFixedWidth(82)
        playButton.clicked.connect(self.playMedia)
        playButton.setIcon(self.icons['play'])
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
