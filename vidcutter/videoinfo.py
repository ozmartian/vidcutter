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

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QSizePolicy, QTextBrowser, QVBoxLayout


class VideoInfo(QDialog):
    modes = {
        'LOW': QSize(450, 300),
        'NORMAL': QSize(600, 450),
        'HIGH': QSize(1080, 700)
    }

    def __init__(self, media, parent=None, flags=Qt.WindowCloseButtonHint):
        super(VideoInfo, self).__init__(parent, flags)
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        if hasattr(self.parent, 'videoService'):
            self.service = self.parent.videoService
        else:
            raise AttributeError('VideoService class unavailable in parent')

        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowModality(Qt.NonModal)
        self.setWindowIcon(self.parent.parent.windowIcon())
        self.setObjectName('mediainfo')
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
        font-family: "Futura LT", sans-serif;
        font-weight: 500;
        font-style: normal;
        text-align: right;
        color: %s;
        white-space: nowrap;
    }
    td { font-weight: normal; }
    h1, h2, h3 { color: %s; }
</style>
<div align="center" style="margin:15px;">%s</div>''' % ('#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                                        '#C681D5' if self.parent.theme == 'dark' else '#642C68',
                                                        self.service.metadata(media))
        content = QTextBrowser(self.parent)
        content.setObjectName('genericdialog2')
        content.setHtml(metadata)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(pixmap=QPixmap(':/images/%s/mediainfo-heading.png' % self.parent.theme)))
        layout.addWidget(content)
        layout.addWidget(buttons)
        self.setLayout(layout)
