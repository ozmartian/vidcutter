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

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QTime
from PyQt5.QtWidgets import QAbstractSpinBox, QLabel, QHBoxLayout, QTimeEdit, QSizePolicy, QWidget


class TimeCounter(QWidget):
    timeChanged = pyqtSignal(QTime)

    def __init__(self, parent=None):
        super(TimeCounter, self).__init__(parent)
        self.parent = parent
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.runtime = QTimeEdit(QTime(0, 0), self)
        self.runtime.setObjectName('timeCounter')
        self.runtime.setFrame(False)
        self.runtime.setDisplayFormat('hh:mm:ss.zzz')
        self.runtime.timeChanged.connect(self.timeChangeHandler)
        separator = QLabel('/', objectName='separator')
        self.duration = QLabel('00:00:00.000', objectName='timeDuration')
        layout = QHBoxLayout(self)
        layout.addWidget(self.runtime)
        layout.addWidget(separator)
        layout.addWidget(self.duration)
        self.setLayout(layout)

    def setRange(self, mintime: str, maxtime: str) -> None:
        self.runtime.setTimeRange(QTime.fromString(mintime, 'hh:mm:ss.zzz'), QTime.fromString(maxtime, 'hh:mm:ss.zzz'))

    def setMinimum(self, mintime: str=None) -> None:
        if mintime is None:
            self.runtime.setMinimumTime(QTime(0, 0))
        else:
            self.runtime.setMinimumTime(QTime.fromString(mintime, 'hh:mm:ss.zzz'))

    def setMaximum(self, maxtime: str) -> None:
        self.runtime.setMaximumTime(QTime.fromString(maxtime, 'hh:mm:ss.zzz'))

    def setTime(self, time: str) -> None:
        self.runtime.setTime(QTime.fromString(time, 'hh:mm:ss.zzz'))

    def setDuration(self, time: str) -> None:
        self.duration.setText(time)
        self.setMaximum(time)

    def clearFocus(self) -> None:
        self.runtime.clearFocus()

    def hasFocus(self) -> bool:
        if self.runtime.hasFocus():
            return True
        return super(TimeCounter, self).hasFocus()

    def setReadOnly(self, readonly: bool) -> None:
        self.runtime.setReadOnly(readonly)
        if readonly:
            self.runtime.setButtonSymbols(QAbstractSpinBox.NoButtons)
        else:
            self.runtime.setButtonSymbols(QAbstractSpinBox.UpDownArrows)

    @pyqtSlot(QTime)
    def timeChangeHandler(self, newtime: QTime) -> None:
        if self.runtime.hasFocus():
            self.timeChanged.emit(newtime)
