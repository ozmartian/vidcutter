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

from enum import Enum

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog, QGroupBox, QHBoxLayout, QVBoxLayout


class StreamSelector(QDialog):

    class Stream(Enum):
        VIDEO = 0,
        AUDIO = 1,
        TEXT = 2,
        METADATA = 3

    def __init__(self, streams: dict, parent=None):
        super(StreamSelector, self).__init__(parent)
        self.parent = parent
        self.streams = streams
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(self.video())
        layout.addWidget(self.audio())
        layout.addWidget(self.subtitles())
        layout.addWidget(self.metadata())
        self.setLayout(layout)

    def video(self) -> QGroupBox:
        return QGroupBox('Video')

    def audio(self) -> QGroupBox:
        return QGroupBox('Audio')

    def subtitles(self) -> QGroupBox:
        return QGroupBox('Subtitles')

    def metadata(self) -> QGroupBox:
        return QGroupBox('Metadata')
