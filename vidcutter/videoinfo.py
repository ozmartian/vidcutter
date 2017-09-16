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

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCloseEvent, QPixmap
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QPushButton, QSizePolicy, QTextBrowser, QHBoxLayout,
                             QVBoxLayout)


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
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle('Media information')
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(self.modes.get(self.parent.parent.scale))
        metadata = '''<style>
    table {
        font-family: "Open Sans", sans-serif;
        font-size: 13px;
        margin-top: -10px;
    }
    td i {
        font-family: "Open Sans", sans-serif;
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
<div align="center" style="margin:15px;">%s</div>''' % ('#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                                        '#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                                        self.parent.videoService.mediainfo(self.media))
        content = QTextBrowser(self.parent)
        content.setStyleSheet('QTextBrowser { border: none; background-color: transparent; }')
        content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content.setHtml(metadata)
        keyframesButton = QPushButton('View Keyframes', self)
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
        # noinspection PyArgumentList
        layout.addWidget(QLabel(pixmap=QPixmap(':/images/%s/mediainfo-heading.png' % self.parent.theme)))
        layout.addWidget(content)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def showKeyframes(self):
        keyframes = self.parent.videoService.getIDRFrames(self.media, formatted_time=True)
        halver = math.ceil(len(keyframes) / 2)
        col1 = keyframes[:halver]
        col2 = keyframes[halver:]
        keyframe_content = '''<style>
            table {
                font-family: "Open Sans", sans-serif;
                font-size: 13px;
                margin-top:-10px;
            }
            td {
                text-align: center;
                font-weight: normal;
            }
        </style>
        <div align="center">
            <table border="0" cellpadding="2" cellspacing="0">
                <tr>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
            </table>
        </div>''' % ('<br/>'.join(col1), '<br/>'.join(col2))
        content = QTextBrowser(self)
        content.setStyleSheet('QTextBrowser { border: none; background-color: transparent; }')
        content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content.setHtml(keyframe_content)
        kframes = QDialog(self, flags=Qt.Dialog | Qt.WindowCloseButtonHint)
        kframes.setObjectName('keyframes')
        kframes.setAttribute(Qt.WA_DeleteOnClose, True)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(kframes.close)
        content_headers = '''<style>
            table {
                font-family: "Futura-Light", sans-serif;
                font-size: 22px;
                font-weight: 500;
                text-align: center;
                color: %s
            }
        </style>
        <table width="230" border="0" cellpadding="8" cellspacing="0">
            <tr>
                <td width="230">Keyframe Timecodes</td>
            </tr>
        </table>
        ''' % ('#C681D5' if self.parent.theme == 'dark' else '#642C68')
        headers = QLabel(content_headers, self)
        layout = QVBoxLayout()
        layout.addWidget(headers)
        layout.addWidget(content)
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel('<b>Total keyframes:</b> %i' % len(keyframes), self), Qt.AlignLeft)
        button_layout.addWidget(buttons, Qt.AlignRight)
        layout.addLayout(button_layout)
        kframes.setLayout(layout)
        kframes.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        kframes.setWindowModality(Qt.WindowModal)
        kframes.setWindowTitle('View Keyframes (IDR)')
        kframes.show()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.deleteLater()
        super(VideoInfo, self).closeEvent(event)
