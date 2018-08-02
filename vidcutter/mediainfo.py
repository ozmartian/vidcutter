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

import logging
import math
import os
import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QStyleFactory,
                             QTextBrowser, QVBoxLayout, qApp)


class MediaInfo(QDialog):
    modes = {
        'LOW': QSize(450, 300),
        'NORMAL': QSize(600, 450),
        'HIGH': QSize(1080, 700)
    }

    def __init__(self, media, parent=None, flags=Qt.Dialog | Qt.WindowCloseButtonHint):
        super(MediaInfo, self).__init__(parent, flags)
        self.logger = logging.getLogger(__name__)
        self.media = media
        self.parent = parent
        self.setObjectName('mediainfo')
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Media information - {}'.format(os.path.basename(self.media)))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(self.modes.get(self.parent.parent.scale))
        if sys.platform in {'win32', 'darwin'}:
            self.setStyle(QStyleFactory.create('Fusion'))
        metadata = '''<style>
    table {{
        font-family: "Noto Sans", sans-serif;
        font-size: 13px;
        border: 1px solid #999;
    }}
    td i {{
        font-family: "Noto Sans", sans-serif;
        font-weight: normal;
        font-style: normal;
        text-align: right;
        color: {pencolor};
        white-space: nowrap;
    }}
    td {{
        font-weight: normal;
        text-align: right;
    }}
    td + td {{ text-align: left; }}
    h1, h2, h3 {{ color: {pencolor}; }}
</style>
<div align="center">{info}</div>'''.format(pencolor='#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                           info=self.parent.videoService.mediainfo(self.media))
        content = QTextBrowser(self.parent)
        if sys.platform in {'win32', 'darwin'}:
            content.setStyle(QStyleFactory.create('Fusion'))
        content.setStyleSheet('''
            QTextBrowser {{
                background-color: {bgcolor};
                color: {pencolor};
                border: 1px solid #999;
            }}'''.format(bgcolor='rgba(12, 15, 16, 210)' if self.parent.theme == 'dark' else 'rgba(255, 255, 255, 150)',
                         pencolor='#FFF' if self.parent.theme == 'dark' else '#000'))
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


class KeyframesDialog(QDialog):
    def __init__(self, keyframes: list, parent=None, flags=Qt.Tool | Qt.FramelessWindowHint):
        super(KeyframesDialog, self).__init__(parent, flags)
        self.parent = parent
        self.setObjectName('keyframes')
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('View keyframes')
        self.setStyleSheet('QDialog { border: 2px solid #000; }')
        self.content = QTextBrowser(self)
        self.content.setStyleSheet('''
            QTextBrowser {{
                border: none;
                border-top: 1px solid {0};
                border-bottom: 1px solid {0};
                background-color: transparent;
        }}'''.format('#4D5355' if parent.parent.theme == 'dark' else '#C0C2C3'))
        self.content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.accepted.connect(self.close)
        buttons.rejected.connect(self.close)
        content_headers = '''<style>
                    table td h2 {{
                        font-family: "Futura LT", sans-serif;
                        font-weight: normal;
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
               font-family: "Noto Sans", sans-serif;
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
        self.content.setHtml(html)
        totalLabel = QLabel('<b>total keyframes:</b> {}'.format(len(keyframes)), self)
        totalLabel.setAlignment(Qt.AlignCenter)
        totalLabel.setObjectName('modalfooter')
        totalLabel.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        button_layout = QHBoxLayout()
        button_layout.addWidget(totalLabel, 1)
        button_layout.addWidget(buttons, 0)
        layout = QVBoxLayout()
        layout.addWidget(headers)
        layout.addWidget(self.content)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.setMinimumWidth(320)
        qApp.restoreOverrideCursor()

    def showEvent(self, event: QShowEvent) -> None:
        if self.content.verticalScrollBar().isVisible() \
                and (self.parent.parent.parent.stylename == 'fusion' or sys.platform in {'win32', 'darwin'}):
            self.content.setStyleSheet('''
                QTextBrowser {{
                    border-left: none;
                    border-right: 1px solid {0};
                    border-top: 1px solid {0};
                    border-bottom: 1px solid {0};
                    background-color: transparent;
                }}'''.format('#4D5355' if self.parent.parent.theme == 'dark' else '#C0C2C3'))
        super(KeyframesDialog, self).showEvent(event)
