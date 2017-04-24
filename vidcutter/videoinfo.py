#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - a simple yet fast & accurate video cutter & joiner
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
import os

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox, QFrame, QHeaderView, QLabel, QPushButton,
                             QSizePolicy, QStyle, QTextBrowser, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)


class VideoInfo(QDialog):
    modes = {
        'LOW': QSize(450, 300),
        'NORMAL': QSize(540, 400),
        'HIGH': QSize(1080, 700)
    }

    def __init__(self, parent=None, flags=Qt.WindowCloseButtonHint):
        super(VideoInfo, self).__init__(parent, flags)
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        if hasattr(self.parent, 'videoService'):
            self.service = self.parent.videoService
        else:
            raise AttributeError('VideoService class unavailable in parent')
        if hasattr(self.parent, 'mediaPlayer'):
            self.player = self.parent.mediaPlayer
        else:
            raise AttributeError('MPV media player unavailable in parent')
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowModality(Qt.NonModal)
        self.setWindowIcon(self.parent.parent.windowIcon())
        self.setObjectName('mediainfo')
        self.setWindowTitle('Media information')
        self.setMinimumSize(self.modes.get(self.parent.parent.scale))

    @staticmethod
    def _label(val) -> QTableWidgetItem:
        item = QTableWidgetItem(val)
        item.setFont(QFont('Open Sans', weight=QFont.Bold))
        item.setForeground(QBrush(Qt.white))
        item.setBackground(QBrush(QColor(106, 69, 114)))
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return item

    @staticmethod
    def _value(val) -> QTableWidgetItem:
        return QTableWidgetItem(val)

    def analyse(self, media: str) -> None:
        streams = self.service.streams(media)
        table = QTableWidget(15, 2, self)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        try:
            table.setItem(0, 0, self._label('filename'))
            table.setItem(0, 1, self._value(os.path.basename(media)))
            table.setItem(1, 0, self._label('audio bitrate'))
            table.setItem(1, 1, self._value(streams.get('audio')[0].get('other_bit_rate')[0]))
            table.setItem(2, 0, self._label('audio channels'))
            table.setItem(2, 1, self._value(streams.get('audio')[0].get('other_channel_s')[0]))
            table.setItem(3, 0, self._label('audio codec'))
            table.setItem(3, 1, self._value(self.player.audio_codec))
            table.setItem(4, 0, self._label('audio frequency'))
            table.setItem(4, 1, self._value(streams.get('audio')[0].get('other_sampling_rate')[0]))
            table.setItem(5, 0, self._label('bitrate'))
            table.setItem(5, 1, self._value(streams.get('general')[0].get('other_overall_bit_rate')[0]))
            table.setItem(6, 0, self._label('color matrix'))
            table.setItem(6, 1, self._value(self.player.colormatrix))
            table.setItem(7, 0, self._label('duration'))
            table.setItem(7, 1, self._value(streams.get('video')[0].get('other_duration')[0]))
            if 'other_writing_library' in streams.get('video')[0].keys():
                table.setItem(8, 0, self._label('encoder'))
                table.setItem(8, 1, self._value(streams.get('video')[0].get('other_writing_library')[0]))
                table.setRowCount(16)
                table.setItem(9, 0, self._label('file size'))
                table.setItem(9, 1, self._value(streams.get('general')[0].get('other_file_size')[0]))
                table.setItem(10, 0, self._label('frame rate'))
                table.setItem(10, 1, self._value(streams.get('general')[0].get('other_frame_rate')[0]))
                table.setItem(11, 0, self._label('frame size'))
                table.setItem(11, 1, self._value('%sx%s' % (self.player.width, self.player.height)))
                table.setItem(12, 0, self._label('pixel aspect ratio'))
                table.setItem(12, 1, self._value(streams.get('video')[0].get('pixel_aspect_ratio')))
                table.setItem(13, 0, self._label('pixel format'))
                table.setItem(13, 1, self._value(self.player.video_out_params.get('pixelformat')))
                table.setItem(14, 0, self._label('video bitrate'))
                table.setItem(14, 1, self._value(streams.get('video')[0].get('other_bit_rate')[0]))
                table.setItem(15, 0, self._label('video codec'))
                table.setItem(15, 1, self._value(self.player.video_codec))
            else:
                table.setItem(8, 0, self._label('file size'))
                table.setItem(8, 1, self._value(streams.get('general')[0].get('other_file_size')[0]))
                table.setItem(9, 0, self._label('frame rate'))
                table.setItem(9, 1, self._value(streams.get('general')[0].get('other_frame_rate')[0]))
                table.setItem(10, 0, self._label('frame size'))
                table.setItem(10, 1, self._value('%sx%s' % (self.player.width, self.player.height)))
                table.setItem(11, 0, self._label('pixel aspect ratio'))
                table.setItem(11, 1, self._value(streams.get('video')[0].get('pixel_aspect_ratio')))
                table.setItem(12, 0, self._label('pixel format'))
                table.setItem(12, 1, self._value(self.player.video_out_params.get('pixelformat')))
                table.setItem(13, 0, self._label('video bitrate'))
                table.setItem(13, 1, self._value(streams.get('video')[0].get('other_bit_rate')[0]))
                table.setItem(14, 0, self._label('video codec'))
                table.setItem(14, 1, self._value(self.player.video_codec))
        except:
            self.logger.error('Error parsing mediainfo properties', exc_info=True)
            self.close()
        buttons = QDialogButtonBox()
        advButton = QPushButton('Advanced')
        advButton.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        buttons.addButton(advButton, QDialogButtonBox.HelpRole)
        buttons.addButton(QDialogButtonBox.Close)
        buttons.helpRequested.connect(lambda: self.advanced(media))
        buttons.rejected.connect(self.close)
        layout = QVBoxLayout()
        layout.addWidget(table)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.show()

    def advanced(self, media: str) -> None:
        self.close()
        advanced = QWidget(self.parent, flags=Qt.Dialog | Qt.WindowCloseButtonHint)
        advanced.setObjectName('mediainfo_advanced')
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(advanced.close)
        metadata = '''
            <style>
                table { font-family: "Open Sans", sans-serif; font-size: 13px; }
                td i { font-weight: 500; font-style: normal; text-align: right; color: %s; }
                td { font-weight: normal; }
                h1, h2, h3 { color: %s; }
            </style>
            <div align="center" style="margin:15px;">%s</div>''' % ('#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                                                    '#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                                                    self.service.metadata(media))
        content = QTextBrowser(self.parent)
        content.setHtml(metadata)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(pixmap=QPixmap(':/images/%s/mediainfo-heading.png' % self.parent.theme)))
        layout.addWidget(content)
        layout.addWidget(buttons)
        advanced.setLayout(layout)
        advanced.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        advanced.setContentsMargins(0, 0, 0, 0)
        advanced.setWindowTitle('Media information (Advanced)')
        if self.parent.parent.scale == 'LOW':
            advanced.setMinimumSize(600, 300)
        else:
            advanced.setMinimumSize(750, 450)
        advanced.show()
