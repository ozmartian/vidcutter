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

import sys
import os

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QFileInfo, QPoint, Qt, QTime, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWidgets import (qApp, QAbstractSpinBox, QCheckBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
                             QProgressBar, QSlider, QSpinBox, QStyle, QStyleFactory, QStyleOptionSlider, QTimeEdit, QToolTip, QWidget)


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
        self.currentframe.setStyle(QStyleFactory.create('fusion'))
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


class VolumeSlider(QSlider):
    def __init__(self, parent=None, **kwargs):
        super(VolumeSlider, self).__init__(parent, **kwargs)
        self.valueChanged.connect(self.showTooltip)
        self.offset = QPoint(0, -45)
        if sys.platform == 'win32':
            self.setStyleSheet('''QSlider::handle { background: #694471; }
                QSlider::handle:hover { background: #A286A8; }
                QSlider::handle:pressed { background: #3D1546; }''')

    @pyqtSlot(int)
    def showTooltip(self, value: int):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        handle = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        globalPos = self.mapToGlobal(handle.topLeft() + self.offset)
        QToolTip.showText(globalPos, str('{0}%'.format(value)), self)


class CompletionMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super(CompletionMessageBox, self).__init__(parent)
        self.parent = parent
        self.theme = self.parent.theme
        self.initIcons()
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setWindowTitle('Operation complete')
        self.setTextFormat(Qt.RichText)
        self.setObjectName('genericdialog3')
        # self.setIconPixmap(self.parent.thumbsupIcon.pixmap(150, 144))
        self.pencolor = '#C681D5' if self.theme == 'dark' else '#642C68'
        self.setText('''
    <style>
        h1 {
            color: %s;
            font-family: "Futura LT", sans-serif;
            font-weight: 400;
        }
        table.info {
            margin: 6px;
            margin-top: 13px;
            padding: 4px 2px;
        }
        td.value {
            font-size: 13px;
            color: %s;
        }
        td.label {
            font-size: 11px;
            color: %s;
            padding-top: 5px;
            text-transform: lowercase;
        }
    </style>
    <h1>Your media is ready!</h1>
    <table class="info" cellpadding="2" cellspacing="0" align="left" width="485">
        <tr>
            <td class="label"><b>File:</b></td>
            <td class="value" nowrap>%s</td>
        </tr>
        <tr>
            <td class="label"><b>Size:</b></td>
            <td class="value">%s</td>
        </tr>
        <tr>
            <td class="label"><b>Length:</b></td>
            <td class="value">%s</td>
        </tr>
    </table><br/>''' % (self.pencolor, ('#EFF0F1' if self.theme == 'dark' else '#222'),
                        self.pencolor, os.path.basename(self.parent.finalFilename),
                        self.parent.sizeof_fmt(int(QFileInfo(self.parent.finalFilename).size())),
                        self.parent.delta2QTime(self.parent.totalRuntime).toString(self.parent.runtimeformat)))
        # self.btn_open = self.addButton('Open', self.ResetRole)
        # self.btn_open.setIcon(self.icon_open)
        # self.btn_open.clicked.connect(lambda: self.openResult(True))
        # btn_restart = self.addButton('Restart', self.AcceptRole)
        # btn_restart.setIcon(self.icon_restart)
        # btn_restart.clicked.connect(self.parent.parent.reboot)
        self.btn_play = self.addButton('Play', self.ResetRole)
        self.btn_play.setIcon(self.icon_play)
        self.btn_play.clicked.connect(lambda: self.openResult(False))
        self.btn_exit = self.addButton('Exit', self.AcceptRole)
        self.btn_exit.setIcon(self.icon_exit)
        self.btn_exit.clicked.connect(self.parent.close)
        btn_continue = self.addButton('Continue', self.AcceptRole)
        btn_continue.setIcon(self.icon_continue)
        btn_continue.clicked.connect(self.close)
        self.setDefaultButton(btn_continue)
        self.setEscapeButton(btn_continue)
        checkbox = QCheckBox('Always show this confirmation box', self)
        checkbox.setChecked(self.parent.showConfirmAction.isChecked())
        checkbox.toggled.connect(self.showConfirm)
        checkbox.setStyleSheet('margin-top:6px; font-size:%s;' % ('11pt' if sys.platform == 'darwin' else '9pt'))
        checkbox.setCursor(Qt.PointingHandCursor)
        self.setCheckBox(checkbox)

    def initIcons(self) -> None:
        self.icon_play = QIcon(':/images/%s/complete-play.png' % self.theme)
        self.icon_open = QIcon(':/images/%s/complete-open.png' % self.theme)
        # self.icon_restart = QIcon(':/images/%s/complete-restart.png' % self.theme)
        self.icon_exit = QIcon(':/images/%s/complete-exit.png' % self.theme)
        self.icon_continue = QIcon(':/images/%s/complete-continue.png' % self.theme)

    @pyqtSlot(bool)
    def showConfirm(self, checked: bool) -> None:
        self.parent.saveSetting('showConfirm', checked)
        self.parent.showConfirmAction.setChecked(checked)

    @pyqtSlot(bool)
    def openResult(self, pathonly: bool = False) -> None:
        if len(self.parent.finalFilename) and os.path.exists(self.parent.finalFilename):
            target = self.parent.finalFilename if not pathonly else os.path.dirname(self.parent.finalFilename)
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))
