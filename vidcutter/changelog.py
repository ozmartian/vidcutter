#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

import sys

from PyQt5.QtCore import QFile, QSize, QTextStream, Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QScrollArea, QSizePolicy, QStyleFactory, QVBoxLayout,
                             qApp)


class Changelog(QDialog):
    def __init__(self, parent=None):
        super(Changelog, self).__init__(parent, Qt.Dialog | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.setWindowTitle('{} changelog'.format(qApp.applicationName()))
        if sys.platform.startswith('linux'):
            filepath = '/usr/share/doc/vidcutter/CHANGELOG'
        else:
            # noinspection PyUnresolvedReferences
            filepath = self.parent.parent.get_path('CHANGELOG', True)
        changelog = QFile(filepath)
        changelog.open(QFile.ReadOnly | QFile.Text)
        content = QTextStream(changelog).readAll()
        label = QLabel(content, self)
        label.setWordWrap(True)
        label.setTextFormat(Qt.PlainText)
        buttons = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.rejected.connect(self.close)
        scrollarea = QScrollArea(self)
        scrollarea.setStyleSheet('QScrollArea { background:transparent; }')
        scrollarea.setWidgetResizable(True)
        scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollarea.setFrameShape(QScrollArea.NoFrame)
        scrollarea.setWidget(label)
        if sys.platform in {'win32', 'darwin'}:
            scrollarea.setStyle(QStyleFactory.create('Fusion'))
        layout = QVBoxLayout()
        layout.addWidget(scrollarea)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setMinimumSize(self.sizeHint())

    def sizeHint(self) -> QSize:
        modes = {
            'LOW': QSize(450, 300),
            'NORMAL': QSize(565, 560),
            'HIGH': QSize(1080, 920)
        }
        return modes[self.parent.parentWidget().scale]
