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
import time

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon, QMouseEvent
from PyQt5.QtWidgets import qApp, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class Notification(QDialog):
    shown = pyqtSignal()
    closed = pyqtSignal()
    duration = 6

    def __init__(self, icon: str, parent=None):
        super(Notification, self).__init__(parent)
        self.parent = parent
        self.theme = self.parent.theme
        self.setObjectName('notification')
        self.setContentsMargins(10, 10, 10, 10)
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.Dialog | Qt.FramelessWindowHint)
        self.setMinimumWidth(550)
        self.shown.connect(lambda: QTimer.singleShot(self.duration * 1000, self.close))
        self._title, self._message = '', ''
        self.buttons = []
        self.msgLabel = QLabel(self._message, self)
        self.msgLabel.setWordWrap(True)
        logo_label = QLabel('<img src="{}" width="82" />'.format(icon), self)
        logo_label.setFixedSize(82, 82)
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(logo_label)
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addLayout(self.left_layout)
        layout.addSpacing(10)
        layout.addWidget(self.msgLabel, Qt.AlignVCenter)
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
        self.msgLabel.setText(value)
        self._message = value

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.close()

    @pyqtSlot()
    def showEvent(self, event):
        if self.isVisible():
            self.shown.emit()
        [self.left_layout.addWidget(btn) for btn in self.buttons]
        super(Notification, self).showEvent(event)

    def closeEvent(self, event):
        event.accept()
        for step in range(100, 0, -10):
            self.setWindowOpacity(step / 100)
            qApp.processEvents()
            time.sleep(0.085)
        self.closed.emit()
        self.deleteLater()
        super(Notification, self).closeEvent(event)


class JobCompleteNotification(Notification):
    def __init__(self, filename: str, filesize: str, runtime: str, icon: str, parent=None):
        super(JobCompleteNotification, self).__init__(icon, parent)
        pencolor = '#C681D5' if self.theme == 'dark' else '#642C68'
        self.filename = filename
        self.filesize = filesize
        self.runtime = runtime
        self.parent = parent
        self.title = 'Your media file is ready!'
        self.message = '''
    <style>
        h1 {{
            color: {labelscolor};
            font-family: "Futura LT", sans-serif;
            font-weight: normal;
            text-align: center;
        }}
        table.info {{
            margin: 6px;
            padding: 4px 2px;
            font-family: "Noto Sans", sans-serif;
        }}
        td.label {{
            font-weight: bold;
            color: {labelscolor};
            text-transform: lowercase;
            text-align: right;
            padding-right: 5px;
            font-size: 14px;
        }}
        td.value {{
            color: {valuescolor};
            font-size: 14px;
        }}
    </style>
    <h1>{heading}</h1>
    <table border="0" class="info" cellpadding="2" cellspacing="0" align="left">
        <tr>
            <td width="20%%" class="label"><b>File:</b></td>
            <td width="80%%" class="value" nowrap>{filename}</td>
        </tr>
        <tr>
            <td width="20%%" class="label"><b>Size:</b></td>
            <td width="80%%" class="value">{filesize}</td>
        </tr>
        <tr>
            <td width="20%%" class="label"><b>Runtime:</b></td>
            <td width="80%%" class="value">{runtime}</td>
        </tr>
    </table>'''.format(labelscolor=pencolor,
                       valuescolor=('#EFF0F1' if self.theme == 'dark' else '#222'),
                       heading=self._title,
                       filename=os.path.basename(self.filename),
                       filesize=self.filesize,
                       runtime=self.runtime)
        playButton = QPushButton(QIcon(':/images/complete-play.png'), 'Play', self)
        playButton.setFixedWidth(82)
        playButton.clicked.connect(self.playMedia)
        playButton.setCursor(Qt.PointingHandCursor)
        self.buttons.append(playButton)

    @pyqtSlot()
    def playMedia(self) -> None:
        if os.path.isfile(self.filename):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.filename))
