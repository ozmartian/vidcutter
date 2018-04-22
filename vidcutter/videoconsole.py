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
import pprint
import sys
from io import StringIO

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QObject
from PyQt5.QtGui import QCloseEvent, QShowEvent, QTextCursor, QTextOption
from PyQt5.QtWidgets import qApp, QDialog, QDialogButtonBox, QStyleFactory, QTextEdit, QVBoxLayout


class VideoConsole(QTextEdit):
    def __init__(self, parent=None):
        super(VideoConsole, self).__init__(parent)
        self._buffer = StringIO()
        self.setReadOnly(True)
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setStyleSheet('QTextEdit { font-family:monospace; font-size:%s; }'
                           % ('10pt' if sys.platform == 'darwin' else '8pt'))
        if sys.platform in {'win32', 'darwin'}:
            self.setStyle(QStyleFactory.create('Fusion'))

    @pyqtSlot(str)
    def write(self, msg):
        self.insertPlainText('%s\n' % msg)
        self.moveCursor(QTextCursor.End)
        self._buffer.write(msg)

    def __getattr__(self, item):
        return getattr(self._buffer, item)


class ConsoleWidget(QDialog):
    def __init__(self, parent=None, flags=Qt.Dialog | Qt.WindowCloseButtonHint):
        super(ConsoleWidget, self).__init__(parent, flags)
        self.parent = parent
        self.edit = VideoConsole(self)
        buttons = QDialogButtonBox()
        buttons.setCenterButtons(True)
        clearButton = buttons.addButton('Clear', QDialogButtonBox.ResetRole)
        clearButton.clicked.connect(self.edit.clear)
        closeButton = buttons.addButton(QDialogButtonBox.Close)
        closeButton.clicked.connect(self.close)
        closeButton.setDefault(True)
        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setWindowTitle('{0} Console'.format(qApp.applicationName()))
        self.setWindowModality(Qt.NonModal)

    def showEvent(self, event: QShowEvent):
        self.parent.consoleLogger.flush()
        super(ConsoleWidget, self).showEvent(event)

    def closeEvent(self, event: QCloseEvent):
        self.parent.cutter.consoleButton.setChecked(False)
        super(ConsoleWidget, self).closeEvent(event)


class ConsoleHandler(QObject, logging.StreamHandler):
    logReceived = pyqtSignal(str)

    def __init__(self, widget):
        QObject.__init__(self)
        logging.StreamHandler.__init__(self)
        self.logReceived.connect(widget.edit.write)

    def emit(self, record):
        self.logReceived.emit(record.message)


class VideoLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super(VideoLogger, self).__init__(name, level)
        self.pp = pprint.PrettyPrinter(indent=2, compact=False)

    def info(self, msg, *args, **kwargs):
        if 'pretty' in list(kwargs.keys()) and kwargs.pop('pretty'):
            msg = self.pp.pformat(msg)
        return super(VideoLogger, self).info(msg, *args, **kwargs)
