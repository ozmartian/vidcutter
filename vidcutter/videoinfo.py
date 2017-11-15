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
import math
import os

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QTextBrowser,
                             QVBoxLayout, qApp)


class VideoInfo(QDialog):
    modes = {
        'LOW': QSize(450, 300),
        'NORMAL': QSize(600, 450),
        'HIGH': QSize(1080, 700)
    }

    def __init__(self, media, parent=None, flags=Qt.Dialog | Qt.WindowCloseButtonHint):
        super(VideoInfo, self).__init__(parent, flags)
        self.logger = logging.getLogger(__name__)
        self.media = media
        self.parent = parent
        self.setObjectName('videoinfo')
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Media information - {}'.format(os.path.basename(self.media)))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(self.modes.get(self.parent.parent.scale))
        metadata = '''<style>
    table {
        font-family: "Noto Sans UI", sans-serif;
        font-size: 13px;
        margin-top: -10px;
    }
    td i {
        font-family: "Noto Sans UI", sans-serif;
        font-weight: normal;
        font-style: normal;
        text-align: right;
        color: %s;
        white-space: nowrap;
    }
    td {
        font-weight: normal;
        text-align: right;
    }
    td + td { text-align: left; }
    h1, h2, h3 { color: %s; }
</style>
<div align="center">%s</div>''' % ('#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                   '#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                   self.parent.videoService.mediainfo(self.media))
        content = QTextBrowser(self.parent)
        content.setStyleSheet('QTextBrowser { border: none; background-color: transparent; }')
        content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content.setHtml(metadata)
        keyframesButton = QPushButton('View keyframes', self)
        keyframesButton.clicked.connect(self.showKeyframes)
        okButton = QDialogButtonBox(QDialogButtonBox.Ok)
        okButton.accepted.connect(self.close)
        button_layout = QHBoxLayout()
        mediainfo_version = self.parent.videoService.cmdExec(self.parent.videoService.backends.mediainfo,
                                                             '--version', True)
        if len(mediainfo_version) >= 2:
            mediainfo_version = mediainfo_version.split('\n')[1]
            mediainfo_label = QLabel('<div style="font-size:11px;"><b>Media information by:</b><br/>%s @ '
                                     % mediainfo_version + '<a href="https://mediaarea.net" target="_blank">' +
                                     'mediaarea.net</a></div>')
            button_layout.addWidget(mediainfo_label)
        button_layout.addStretch(1)
        button_layout.addWidget(keyframesButton)
        button_layout.addWidget(okButton)
        layout = QVBoxLayout()
        layout.addWidget(content)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def showKeyframes(self):
        qApp.setOverrideCursor(Qt.WaitCursor)
        keyframes = self.parent.videoService.getKeyframes(self.media, formatted_time=True)
        kframes = KeyframesDialog(keyframes, self)
        kframes.show()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.deleteLater()
        super(VideoInfo, self).closeEvent(event)


class KeyframesDialog(QDialog):
    def __init__(self, keyframes: list, parent=None, flags=Qt.Tool | Qt.FramelessWindowHint):
        super(KeyframesDialog, self).__init__(parent, flags)
        self.setObjectName('keyframes')
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('View keyframes')
        self.setStyleSheet('QDialog { border: 2px solid #000; }')
        content = QTextBrowser(self)
        content.setStyleSheet('QTextBrowser { border: none; background-color: transparent; }')
        content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.accepted.connect(self.close)
        buttons.rejected.connect(self.close)
        content_headers = '''<style>
                    table td h2 {{
                        font-family: "Futura-Light", sans-serif;
                        font-weight: 500;
                        text-align: center;
                        color: {}
                    }}
                </style>
                <table width="300" border="0" cellpadding="4" cellspacing="0">
                    <tr>
                        <td><h2>Keyframe Timecodes</h2></td>
                    </tr>
                </table>
                '''.format('#C681D5' if parent.parent.theme == 'dark' else '#642C68')
        headers = QLabel(content_headers, self)
        halver = math.ceil(len(keyframes) / 2)
        col1 = '<br/>'.join(keyframes[:halver])
        col2 = '<br/>'.join(keyframes[halver:])
        html = '''<style>
            table {{
               font-family: "Noto Sans UI", sans-serif;
               font-size: 13px;
           }}
           td {{
               text-align: center;
               font-weight: normal;
           }}
        </style>
        <div align="center">
           <table border="0" cellpadding="2" cellspacing="0">
               <tr>
                   <td>{col1}</td>
                   <td>{col2}</td>
               </tr>
           </table>
        </div>'''.format(**locals())
        content.setHtml(html)
        totalLabel = QLabel('<b>total keyframes:</b> {}'.format(len(keyframes)), self)
        totalLabel.setAlignment(Qt.AlignCenter)
        totalLabel.setObjectName('modalfooter')
        totalLabel.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        button_layout = QHBoxLayout()
        button_layout.addWidget(totalLabel, 1)
        button_layout.addWidget(buttons, 0)
        layout = QVBoxLayout()
        layout.addWidget(headers)
        layout.addWidget(content)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.setMinimumWidth(320)
        qApp.restoreOverrideCursor()
