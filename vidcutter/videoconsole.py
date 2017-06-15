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
from io import StringIO

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import qApp, QTextEdit


class VideoConsole(QTextEdit):
    def __init__(self, parent=None):
        super(VideoConsole, self).__init__(parent)
        self.parent = parent
        self._buffer = StringIO()
        self.setReadOnly(True)
        # self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setWindowModality(Qt.NonModal)
        self.setWindowTitle('{0} Console'.format(qApp.applicationName()))

    def write(self, msg):
        self.insertPlainText(msg)
        self.moveCursor(QTextCursor.End)
        self._buffer.write(msg)

    def __getattr__(self, item):
        return getattr(self._buffer, item)


# class WidgetHandler(logging.Handler):
#     def __init__(self, widget):
#         super(WidgetHandler, self).__init__()
#         self._widget = widget
#
#     @property
#     def widget(self):
#         return self._widget
#
#     def emit(self, record):
#         self._widget.write(self.format(record))


class ConsoleLogger(logging.Handler):
    edit = VideoConsole()

    def emit(self, record):
        self.edit.write(msg=self.format(record))
