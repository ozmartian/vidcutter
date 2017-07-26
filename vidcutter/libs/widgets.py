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

import os
import sys

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QEvent, QObject, QPoint, Qt, QTime
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import (qApp, QAbstractSpinBox, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel,
                             QMessageBox, QProgressBar, QSlider, QSpinBox, QStyle, QStyleFactory, QStyleOptionSlider,
                             QTimeEdit, QToolBox, QToolTip, QVBoxLayout, QWidget)

if sys.platform.startswith('linux'):
    from vidcutter.libs.taskbarprogress import TaskbarProgress


class TimeCounter(QWidget):
    timeChanged = pyqtSignal(QTime)

    def __init__(self, parent=None):
        super(TimeCounter, self).__init__(parent)
        self.parent = parent
        self.timeedit = QTimeEdit(QTime(0, 0))
        self.timeedit.setObjectName('timeCounter')
        self.timeedit.setStyle(QStyleFactory.create('fusion'))
        self.timeedit.setFrame(False)
        self.timeedit.setDisplayFormat('hh:mm:ss.zzz')
        self.timeedit.timeChanged.connect(self.timeChangeHandler)
        separator = QLabel('/')
        separator.setObjectName('timeSeparator')
        self.duration = QLabel('00:00:00.000')
        self.duration.setObjectName('timeDuration')
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
        self.currentframe = QSpinBox(self)
        self.currentframe.setObjectName('frameCounter')
        self.currentframe.setStyle(QStyleFactory.create('fusion'))
        self.currentframe.setFrame(False)
        self.currentframe.setAlignment(Qt.AlignRight)
        self.currentframe.valueChanged.connect(self.frameChangeHandler)
        separator = QLabel('/')
        separator.setObjectName('frameSeparator')
        self.framecount = QLabel('0000')
        self.framecount.setObjectName('frameCount')
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
        self.parent = parent
        if sys.platform.startswith('linux'):
            self.taskbar = TaskbarProgress(self)
        self._progress = QProgressBar(self.parent)
        self._progress.setRange(0, 0)
        self._progress.setTextVisible(False)
        self._progress.setStyle(QStyleFactory.create('fusion'))
        self._label = QLabel(parent)
        self._label.setAlignment(Qt.AlignCenter)
        layout = QGridLayout()
        layout.addWidget(self._progress, 0, 0)
        layout.addWidget(self._label, 0, 0)
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(500)
        self.setLayout(layout)

    def value(self) -> int:
        return self._progress.value()

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
        if sys.platform.startswith('linux'):
            self.taskbar.setProgress(float(val / self._progress.maximum()), True)
        self._progress.setValue(val)

    def updateProgress(self, value: int, text: str) -> None:
        self.setValue(value)
        self.setText(text)
        qApp.processEvents()

    @pyqtSlot()
    def close(self) -> None:
        if sys.platform.startswith('linux'):
            self.taskbar.clear()
        self.deleteLater()
        super(VCProgressBar, self).close()


class VolumeSlider(QSlider):
    def __init__(self, parent=None, **kwargs):
        super(VolumeSlider, self).__init__(parent, **kwargs)
        self.setObjectName('volumeslider')
        self.valueChanged.connect(self.showTooltip)
        self.offset = QPoint(0, -45)
        self.setStyle(QStyleFactory.create('Fusion'))

    @pyqtSlot(int)
    def showTooltip(self, value: int) -> None:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        handle = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        pos = handle.topLeft()
        pos += self.offset
        globalPos = self.mapToGlobal(pos)
        QToolTip.showText(globalPos, str('{0}%'.format(value)), self)


class ClipErrorsDialog(QDialog):

    class VCToolBox(QToolBox):
        def __init__(self, parent=None, **kwargs):
            super(ClipErrorsDialog.VCToolBox, self).__init__(parent, **kwargs)
            self.parent = parent
            self.installEventFilter(self)

        def showEvent(self, event: QShowEvent):
            self.adjustSize()
            self.parent.adjustSize()

        def eventFilter(self, obj: QObject, event: QEvent) -> bool:
            if event.type() == QEvent.Enter:
                qApp.setOverrideCursor(Qt.PointingHandCursor)
            elif event.type() == QEvent.Leave:
                qApp.restoreOverrideCursor()
            return super(ClipErrorsDialog.VCToolBox, self).eventFilter(obj, event)

    def __init__(self, errors: list, parent=None, flags=Qt.WindowCloseButtonHint):
        super(ClipErrorsDialog, self).__init__(parent, flags)
        self.errors = errors
        self.parent = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Cannot add media file(s)')
        self.headingcolor = '#C681D5' if self.parent.theme == 'dark' else '#642C68'
        self.pencolor = '#FFF' if self.parent.theme == 'dark' else '#222'
        self.toolbox = ClipErrorsDialog.VCToolBox(self)
        self.toolbox.currentChanged.connect(self.selectItem)
        self.detailedLabel = QLabel(self)
        self.buttons = QDialogButtonBox(self)
        closebutton = self.buttons.addButton(QDialogButtonBox.Close)
        closebutton.clicked.connect(self.close)
        closebutton.setDefault(True)
        closebutton.setAutoDefault(True)
        closebutton.setCursor(Qt.PointingHandCursor)
        closebutton.setFocus()
        introLabel = self.intro()
        introLabel.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addWidget(introLabel)
        layout.addSpacing(10)
        layout.addWidget(self.toolbox)
        layout.addSpacing(10)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
        self.parseErrors()

    def intro(self) -> QLabel:
        return QLabel('''
        <style>
            h1 {
                text-align: center;
                color: %s;
                font-family: "Futura-Light", sans-serif;
                font-weight: 400;
            }
            p {
                font-family: "Open Sans", sans-serif;
                color: %s;
            }
        </style>
        <h1>Invalid media files detected</h1>
        <p>
            One or more media files were prevented from being added to your project. Each rejected file is listed below.
            Clicking on filenames will reveal error information explaining why it was not added. 
        </p>
        ''' % (self.headingcolor, self.pencolor))

    def selectItem(self, index: int) -> None:
        self.toolbox.adjustSize()
        self.adjustSize()

    def parseErrors(self) -> None:
        for file, error in self.errors:
            if not len(error):
                error = '<div align="center">Invalid media file.<br/><br/>This is not a media file or the file ' + \
                        'is irreversibly corrupt.</div>'
            errorLabel = QLabel(error, self)
            index = self.toolbox.addItem(errorLabel, os.path.basename(file))
            self.toolbox.setItemToolTip(index, file)

    def setDetailedMessage(self, msg: str) -> None:
        msg = '''
        <style>
            h1 {
                text-align: center;
                color: %s;
                font-family: "Futura-Light", sans-serif;
                font-weight: 400;
            }
            p {
                font-family: "Open Sans", sans-serif;
                font-weight: 300;
                color: %s;
            }
        </style>
        <h1>Help :: Adding media files</h1>
        %s''' % (self.headingcolor, self.pencolor, msg)
        helpbutton = self.buttons.addButton('Help', QDialogButtonBox.ResetRole)
        helpbutton.setCursor(Qt.PointingHandCursor)
        helpbutton.clicked.connect(lambda: QMessageBox.information(self, 'Help :: Adding Media Files', msg,
                                                                   QMessageBox.Ok))
