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

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QTime
from PyQt5.QtWidgets import (QAbstractSpinBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QSpinBox,
                             QStyle, QStyleFactory, QTimeEdit, QWidget)


class TimeCounter(QWidget):
    timeChanged = pyqtSignal(QTime)

    def __init__(self, parent=None):
        super(TimeCounter, self).__init__(parent)
        self.parent = parent
        self.timeedit = QTimeEdit(QTime(0, 0), self, objectName='timeCounter')
        self.timeedit.setStyle(QStyleFactory.create('fusion'))
        self.timeedit.setFrame(False)
        self.timeedit.setDisplayFormat('hh:mm:ss.zzz')
        self.timeedit.timeChanged.connect(self.timeChangeHandler)
        separator = QLabel('/', objectName='timeSeparator')
        self.duration = QLabel('00:00:00.000', objectName='timeDuration')
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.timeedit)
        layout.addWidget(separator)
        layout.addWidget(self.duration)
        self.setLayout(layout)

    def setRange(self, minval: str, maxval: str) -> None:
        self.timeedit.setTimeRange(QTime.fromString(minval, 'hh:mm:ss.zzz'),
                                   QTime.fromString(maxval, 'hh:mm:ss.zzz'))

    def setMinimum(self, val: str = None) -> None:
        if val is None:
            self.timeedit.setMinimumTime(QTime(0, 0))
        else:
            self.timeedit.setMinimumTime(QTime.fromString(val, 'hh:mm:ss.zzz'))

    def setMaximum(self, val: str) -> None:
        self.timeedit.setMaximumTime(QTime.fromString(val, 'hh:mm:ss.zzz'))

    def setTime(self, time: str) -> None:
        self.timeedit.setTime(QTime.fromString(time, 'hh:mm:ss.zzz'))

    def setDuration(self, time: str) -> None:
        self.duration.setText(time)
        self.setMaximum(time)

    def clearFocus(self) -> None:
        self.timeedit.clearFocus()

    def hasFocus(self) -> bool:
        if self.timeedit.hasFocus():
            return True
        return super(TimeCounter, self).hasFocus()

    def reset(self) -> None:
        self.timeedit.setTime(QTime(0, 0))
        self.setDuration('00:00:00.000')

    def setReadOnly(self, readonly: bool) -> None:
        self.timeedit.setReadOnly(readonly)
        if readonly:
            self.timeedit.setButtonSymbols(QAbstractSpinBox.NoButtons)
        else:
            self.timeedit.setButtonSymbols(QAbstractSpinBox.UpDownArrows)

    @pyqtSlot(QTime)
    def timeChangeHandler(self, newtime: QTime) -> None:
        if self.timeedit.hasFocus():
            self.timeChanged.emit(newtime)


class FrameCounter(QWidget):
    frameChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super(FrameCounter, self).__init__(parent)
        self.parent = parent
        self.currentframe = QSpinBox(self, objectName='frameCounter')
        self.currentframe.setFrame(False)
        self.currentframe.setAlignment(Qt.AlignRight)
        self.currentframe.valueChanged.connect(self.frameChangeHandler)
        separator = QLabel('/', objectName='frameSeparator')
        self.framecount = QLabel('0000', objectName='frameCount')
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.currentframe)
        layout.addWidget(separator)
        layout.addWidget(self.framecount)
        self.setLayout(layout)

    def setRange(self, minval: int, maxval: int) -> None:
        self.currentframe.setRange(minval, maxval)

    def lockMinimum(self) -> None:
        self.currentframe.setMinimum(self.currentframe.value())

    def setMaximum(self, val: int) -> None:
        self.currentframe.setMaximum(val)

    def setFrame(self, frame: int) -> None:
        self.currentframe.setValue(frame)

    def setFrameCount(self, count: int) -> None:
        self.framecount.setText(str(count))
        self.setMaximum(count)

    def hasFocus(self) -> bool:
        if self.currentframe.hasFocus():
            return True
        return super(FrameCounter, self).hasFocus()

    def clearFocus(self) -> None:
        self.currentframe.clearFocus()

    def reset(self) -> None:
        self.setFrame(0)
        self.setFrameCount(0)

    def setReadOnly(self, readonly: bool) -> None:
        self.currentframe.setReadOnly(readonly)
        if readonly:
            self.currentframe.setButtonSymbols(QAbstractSpinBox.NoButtons)
        else:
            self.currentframe.setButtonSymbols(QAbstractSpinBox.UpDownArrows)

    @pyqtSlot(int)
    def frameChangeHandler(self, frame: int) -> None:
        if self.currentframe.hasFocus():
            self.frameChanged.emit(frame)


class VCProgressBar(QDialog):
    def __init__(self, parent=None, flags=Qt.FramelessWindowHint):
        super(VCProgressBar, self).__init__(parent, flags)
        self._progress = QProgressBar(parent)
        self._progress.setRange(0, 0)
        self._progress.setTextVisible(False)
        self._progress.setStyle(QStyleFactory.create('fusion'))
        self._label = QLabel(parent)
        self._label.setAlignment(Qt.AlignCenter)
        layout = QGridLayout()
        layout.addWidget(self._progress, 0, 0)
        layout.addWidget(self._label, 0, 0)
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(400)
        self.setLayout(layout)

    def setStyle(self, style: QStyle) -> None:
        self._progress.setStyle(style)

    def setText(self, val: str) -> None:
        self._label.setText(val)

    def setMinimum(self, val: int) -> None:
        self._progress.setMinimum(val)

    def setMaximum(self, val: int) -> None:
        self._progress.setMaximum(val)

    def setRange(self, minval: int, maxval: int) -> None:
        self._progress.setRange(minval, maxval)

    def setValue(self, val: int) -> None:
        self._progress.setValue(val)
