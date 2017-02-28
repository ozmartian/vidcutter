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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget


class MediaInfo(QWidget):
    def __init__(self, parent, mpv: object, flags=Qt.Dialog | Qt.WindowCloseButtonHint):
        super(MediaInfo, self).__init__(parent, flags=flags)
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        self.mpv = mpv
        layout = QVBoxLayout(spacing=0)
        layout.addWidget(QLabel(pixmap=QPixmap(':/images/mediainfo-heading.png')))
        layout.addWidget(self.get_metadata())
        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle('Media Information')
        self.setMinimumSize(400, 300)

    def get_metadata(self) -> QTextBrowser:
        self.data = '''
<style>
    * { font-family: "Open Sans", sans-serif; font-size:9pt; }
    .prop { font-weight:bold; text-align:right; }
    table { background:transparent; }
</style>
<div align="center">
    <table width="350" border="0" cellpadding="3" cellspacing="0">'''
        self.add_item('Filename', str(self.mpv.filename, 'utf-8'))
        self.add_item('Duration', self.parent.delta2QTime(self.mpv.duration * 1000).toString(self.parent.runtimeformat))
        self.add_item('File Size', self.parent.sizeof_fmt(int(self.mpv.file_size)))
        self.data += '</div></table>'
        doc = QTextBrowser(self)
        doc.setHtml(self.data)
        return doc

    def add_item(self, prop: str, val: str):
        self.data += '<tr><td class="prop">%s</td><td>:</td><td class="val" width="100%%">%s</td></tr>' % (prop, val)

    @staticmethod
    def general_props() -> list:
        return [
            'filename',
            'file_format',
            'icc_profile',
            'icc_profile_auto',
            'vd_lavc_check_hw_profile',
            'file_size',
            'duration',
            'encoder_list'
        ]

    @staticmethod
    def video_props() -> list:
        return [
            'media_title',
            'video_aspect',
            'video_bitrate',
            'video_codec',
            'video_format',
            'video_frame_info',
            'video_output_levels',
            'video_pan_x',
            'video_pan_y',
            'video_params',
            'video_rotate',
            'video_speed_correction',
            'video_zoom'
        ]

    @staticmethod
    def audio_props() -> list:
        return [
            'audio_bitrate',
            'audio_channels',
            'audio_codec',
            'audio_codec_name',
            'audio_delay',
            'audio_device',
            # 'audio_device_list',
            'audio_out_detected_device',
            'audio_params',
            'audio_samplerate',
            'audio_speed_correction'
        ]
