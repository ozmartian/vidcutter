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

from PyQt5.QtCore import pyqtSignal, Qt, QTime
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel, QTimeEdit, QSizePolicy, QStackedLayout, QWidget


class TimeCounter(QWidget):
    def __init__(self, parent=None):
        super(TimeCounter, self).__init__(parent)
        self.tc_label = ClickableLabel('00:00:00 / 00:00:00', autoFillBackground=True, alignment=Qt.AlignCenter,
                                       sizePolicy=QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.tc_label.setObjectName('timeCounter')
        self.tc_input = QTimeEdit(QTime.fromString(self.tc_label.text()), self)
        self.tc_input.setObjectName('timeInput')
        self.tc_input.setFrame(False)
        self.layout = QStackedLayout(self)
        self.layout.addWidget(self.tc_label)
        self.layout.addWidget(self.tc_input)
        self.setLayout(self.layout)
        self.setContentsMargins(0, 0, 0, 0)
        # self.tc_label.clicked.connect(self.toggleField)

    def setText(self, text: str):
        self.tc_label.setText(text)

    def toggleField(self):
        if self.layout.currentIndex() == 1:
            self.layout.setCurrentIndex(0)
        else:
            self.layout.setCurrentIndex(1)
            self.tc_input.setTime(QTime.fromString(self.tc_label.text()))
            self.tc_input.setFocus()


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None, *arg, **kwargs):
        super(ClickableLabel, self).__init__(parent, *arg, **kwargs)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit()
