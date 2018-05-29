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

import os
import sys
from typing import Union

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation, Qt, QSize,
                          QTime, QTimer)
from PyQt5.QtGui import QFocusEvent, QMouseEvent, QPixmap, QShowEvent
from PyQt5.QtWidgets import (qApp, QDialog, QDialogButtonBox, QDoubleSpinBox, QGraphicsOpacityEffect, QGridLayout,
                             QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox, QProgressBar, QPushButton, QSlider,
                             QSpinBox, QStyle, QStyleFactory, QStyleOptionSlider, QTimeEdit, QToolBox, QToolTip,
                             QVBoxLayout, QWidget, QWidgetAction)


class VCToolBarButton(QWidget):
    clicked = pyqtSignal(bool)

    def __init__(self, label: str, statustip: str, labelstyle: str='beside', parent=None):
        super(VCToolBarButton, self).__init__(parent)
        self.setFocusPolicy(Qt.NoFocus)
        self.button = QPushButton(parent)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setFlat(True)
        self.button.setFixedSize(QSize(50, 53))
        self.button.installEventFilter(self)
        self.button.clicked.connect(self.clicked)
        self.setup(label, statustip)
        self.label1 = QLabel(label.replace(' ', '<br/>'), self)
        self.label2 = QLabel(label, self)
        self.label2.setAlignment(Qt.AlignHCenter)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.button, 0, 0, Qt.AlignHCenter)
        layout.addWidget(self.label1, 0, 1)
        layout.addWidget(self.label2, 1, 0)
        self.setLayout(layout)
        self.setLabelStyle(labelstyle)

    def setup(self, label: str, statustip: str, reset: bool=False) -> None:
        self.button.setToolTip(label)
        self.button.setStatusTip(statustip)
        self.button.setObjectName('toolbar-{}'.format(label.split()[0].lower()))
        if reset:
            self.label1.setText(label.replace(' ', '<br/>'))
            self.label2.setText(label)
            self.button.setStyleSheet('')

    def setLabelStyle(self, labelstyle: str) -> None:
        if labelstyle == 'under':
            self.label1.setVisible(False)
            self.label2.setVisible(True)
        elif labelstyle == 'none':
            self.label1.setVisible(False)
            self.label2.setVisible(False)
        else:
            self.label1.setVisible(True)
            self.label2.setVisible(False)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() in {QEvent.ToolTip, QEvent.StatusTip} and not self.isEnabled():
            return True
        return super(VCToolBarButton, self).eventFilter(obj, event)


class VCTimeCounter(QWidget):
    timeChanged = pyqtSignal(QTime)

    def __init__(self, parent=None):
        super(VCTimeCounter, self).__init__(parent)
        self.parent = parent
        self.timeedit = QTimeEdit(QTime(0, 0))
        self.timeedit.setObjectName('timeCounter')
        self.timeedit.setStyle(QStyleFactory.create('Fusion'))
        self.timeedit.setFrame(False)
        self.timeedit.setDisplayFormat('hh:mm:ss.zzz')
        self.timeedit.timeChanged.connect(self.timeChangeHandler)
        self.timeedit.setCurrentSectionIndex(3)
        separator = QLabel('/')
        separator.setObjectName('timeSeparator')
        self.duration = QLabel('00:00:00.000')
        self.duration.setObjectName('timeDuration')
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
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
        return self.timeedit.hasFocus()

    def reset(self) -> None:
        self.timeedit.setTime(QTime(0, 0))
        self.setDuration('00:00:00.000')

    def setReadOnly(self, readonly: bool) -> None:
        self.timeedit.setReadOnly(readonly)
        if readonly:
            self.timeedit.setButtonSymbols(QTimeEdit.NoButtons)
        else:
            self.timeedit.setButtonSymbols(QTimeEdit.UpDownArrows)

    @pyqtSlot(QTime)
    def timeChangeHandler(self, newtime: QTime) -> None:
        if self.timeedit.hasFocus():
            self.timeChanged.emit(newtime)


class VCFrameCounter(QWidget):
    frameChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super(VCFrameCounter, self).__init__(parent)
        self.parent = parent
        self.currentframe = QSpinBox(self)
        self.currentframe.setObjectName('frameCounter')
        self.currentframe.setStyle(QStyleFactory.create('Fusion'))
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
        return self.currentframe.hasFocus()

    def clearFocus(self) -> None:
        self.currentframe.clearFocus()

    def reset(self) -> None:
        self.setFrame(0)
        self.setFrameCount(0)

    def setReadOnly(self, readonly: bool) -> None:
        self.currentframe.setReadOnly(readonly)
        if readonly:
            self.currentframe.setButtonSymbols(QSpinBox.NoButtons)
        else:
            self.currentframe.setButtonSymbols(QSpinBox.UpDownArrows)

    @pyqtSlot(int)
    def frameChangeHandler(self, frame: int) -> None:
        if self.currentframe.hasFocus():
            self.frameChanged.emit(frame)


class VCProgressDialog(QDialog):
    taskbarprogress = pyqtSignal(float, bool)

    def __init__(self, parent=None, flags=Qt.Dialog | Qt.FramelessWindowHint, modal: bool=True):
        super(VCProgressDialog, self).__init__(parent, flags)
        self.parent = parent
        if modal:
            self.setWindowModality(Qt.ApplicationModal)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setStyleSheet('QDialog { border: 2px solid #000; }')
        self._progress = QProgressBar(self)
        self._progress.setRange(0, 0)
        self._progress.setTextVisible(False)
        self._progress.setStyle(QStyleFactory.create('Fusion'))
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        layout = QGridLayout()
        layout.addWidget(self._progress, 0, 0)
        layout.addWidget(self._label, 0, 0)
        self._timerprefix = QLabel('<b>Elapsed time:</b>', self)
        self._timerprefix.setObjectName('progresstimer')
        self._timervalue = QLabel(self)
        self._timervalue.setObjectName('progresstimer')
        timerlayout = QHBoxLayout()
        timerlayout.addWidget(self._timerprefix)
        timerlayout.addWidget(self._timervalue)
        self._timerwidget = QWidget(self)
        self._timerwidget.setLayout(timerlayout)
        self._timerwidget.hide()
        self._time = QTime()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.updateTimer)
        self.setLayout(layout)
        self.setFixedWidth(550)

    def reset(self, steps: int=0, timer: bool=False) -> None:
        self.setValue(0)
        self.setRange(0, steps)
        self.setText('Analyzing video source')
        self.showTimer() if timer else self.hideTimer()

    def showTimer(self) -> None:
        self._timerwidget.show()
        # noinspection PyArgumentList
        self.layout().addWidget(self._timerwidget, 1, 0, Qt.AlignHCenter | Qt.AlignTop)
        self._time.start()
        self.updateTimer()
        self._timer.start(1000)

    def hideTimer(self) -> None:
        self._timerwidget.hide()
        self.layout().removeWidget(self._timerwidget)

    @pyqtSlot()
    def updateTimer(self) -> None:
        secs = self._time.elapsed() / 1000
        mins = int(secs / 60) % 60
        hrs = int(secs / 3600)
        secs = int(secs % 60)
        elapsed = '{hrs:02d}:{mins:02d}:{secs:02d}'.format(**locals())
        self._timervalue.setText(elapsed)

    def value(self) -> int:
        return self._progress.value()

    def setStyle(self, style: QStyle) -> None:
        self._progress.setStyle(style)

    def setText(self, val: str) -> None:
        if '<b>' in val:
            css = '<style>b { font-family:"Noto Sans"; font-weight:bold; }</style>'
            val = '{0}{1}'.format(css, val)
        self._label.setText(val)

    def setMinimum(self, val: int) -> None:
        self._progress.setMinimum(val)

    def setMaximum(self, val: int) -> None:
        self._progress.setMaximum(val)

    @pyqtSlot(int, int)
    def setRange(self, minval: int, maxval: int) -> None:
        self._progress.setRange(minval, maxval)

    def setValue(self, val: int) -> None:
        if sys.platform.startswith('linux') and self._progress.maximum() != 0:
            self.taskbarprogress.emit(float(val / self._progress.maximum()), True)
        self._progress.setValue(val)
        if val >= self._progress.maximum() and self._timer.isActive():
            self._timer.stop()

    @pyqtSlot(str)
    def updateProgress(self, text: str) -> None:
        self.setValue(self._progress.value() + 1)
        self.setText(text)
        qApp.processEvents()

    @pyqtSlot()
    def close(self) -> None:
        if sys.platform.startswith('linux'):
            self.taskbarprogress.emit(0.0, False)
        if self._timer.isActive():
            self._timer.stop()
        super(VCProgressDialog, self).close()

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.activateWindow()
        self.setFocus()


class VCVolumeSlider(QSlider):
    def __init__(self, parent=None, **kwargs):
        super(VCVolumeSlider, self).__init__(parent, **kwargs)
        self.setObjectName('volumeslider')
        self.setFocusPolicy(Qt.NoFocus)
        self.valueChanged.connect(self.showTooltip)
        self.offset = QPoint(0, -45)
        if sys.platform in {'win32', 'darwin'}:
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


class VCInputDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, label: str, text: str):
        super(VCInputDialog, self).__init__(parent, Qt.Dialog | Qt.WindowCloseButtonHint)
        self.input = QLineEdit(text, self)
        self.input.setStyle(QStyleFactory.create('Fusion'))
        self.input.setClearButtonEnabled(True)
        self.input.selectAll()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label, self))
        layout.addWidget(self.input)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setWindowTitle(title)
        self.setFixedSize(350, self.sizeHint().height())


class VCDoubleInputDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, label: str, value: float, minval: float, maxval: float,
                 decimals: int, step: float, desc: str=None, suffix: str=None):
        super(VCDoubleInputDialog, self).__init__(parent, Qt.Dialog | Qt.WindowCloseButtonHint)
        self._spinbox = QDoubleSpinBox(self)
        self._spinbox.setStyle(QStyleFactory.create('Fusion'))
        self._spinbox.setAttribute(Qt.WA_MacShowFocusRect, False)
        self._spinbox.setDecimals(decimals)
        self._spinbox.setRange(minval, maxval)
        self._spinbox.setSingleStep(step)
        if suffix is not None:
            self._spinbox.setSuffix(' {}'.format(suffix))
        self.value = value
        startbutton = QPushButton('Start')
        startbutton.setDefault(True)
        self.buttons = QDialogButtonBox(self)
        self.buttons.addButton(startbutton, QDialogButtonBox.AcceptRole)
        self.buttons.addButton(QDialogButtonBox.Cancel)
        self.buttons.rejected.connect(self.close)
        fieldlayout = QHBoxLayout()
        fieldlayout.addWidget(QLabel(label, self))
        fieldlayout.addWidget(self._spinbox)
        layout = QVBoxLayout()
        layout.addLayout(fieldlayout)
        if desc is not None:
            desc_label = QLabel(desc, self)
            desc_label.setTextFormat(Qt.RichText)
            desc_label.setObjectName('dialogdesc')
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
        self.setWindowTitle(title)

    @property
    def value(self) -> float:
        return self._spinbox.value()

    @value.setter
    def value(self, val: float) -> None:
        self._spinbox.setValue(val)


class VCBlinkText(QWidget):
    def __init__(self, text: str, parent=None):
        super(VCBlinkText, self).__init__(parent)
        self.label = QLabel(text)
        self.label.setMinimumHeight(self.label.sizeHint().height() + 20)
        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        self.effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b'opacity')
        self.anim.setDuration(3500)
        self.anim.setLoopCount(-1)
        self.anim.setStartValue(1.0)
        self.anim.setKeyValueAt(0.5, 0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.start(QPropertyAnimation.DeleteWhenStopped)

    def setAlignment(self, alignment: Qt.AlignmentFlag) -> None:
        self.label.setAlignment(alignment)

    def stop(self) -> None:
        self.anim.stop()


class VCFilterMenuAction(QWidgetAction):

    class VCFilterMenuWidget(QWidget):
        triggered = pyqtSignal()

        def __init__(self, icon: QPixmap, title: str, text: str, subtext: str):
            super(VCFilterMenuAction.VCFilterMenuWidget, self).__init__()
            self.icon_label = QLabel(self)
            self.icon_label.setPixmap(icon)
            self.text_label = QLabel('<b>{title}:</b> {text}<br/><font size="-1">{subtext}</font>'.format(**locals()),
                                     self)
            layout = QHBoxLayout()
            layout.addWidget(self.icon_label)
            layout.addSpacing(5)
            layout.addWidget(self.text_label)
            self.setLayout(layout)

        def mousePressEvent(self, event: QMouseEvent) -> None:
            if event.button() == Qt.LeftButton:
                self.triggered.emit()
            super(VCFilterMenuAction.VCFilterMenuWidget, self).mousePressEvent(event)

        def enterEvent(self, event: QEvent) -> None:
            if self.isEnabled():
                self.parentWidget().setStyleSheet('background-color: palette(highlight); '
                                                  'color: palette(highlighted-text);')
            super(VCFilterMenuAction.VCFilterMenuWidget, self).enterEvent(event)

        def leaveEvent(self, event: QEvent) -> None:
            if self.isEnabled():
                self.parentWidget().setStyleSheet('background-color: palette(window); color: palette(text);')
            super(VCFilterMenuAction.VCFilterMenuWidget, self).leaveEvent(event)

    def __init__(self, icon: QPixmap, title: str, text: str, subtext: str, parent=None):
        super(VCFilterMenuAction, self).__init__(parent)
        self.setStatusTip(text)
        w = VCFilterMenuAction.VCFilterMenuWidget(icon, title, text, subtext)
        w.triggered.connect(self.trigger)
        self.setDefaultWidget(w)


class VCMessageBox(QMessageBox):
    def __init__(self, title: str, heading: str, text: str, buttons: Union=None, width: int=350, parent: QWidget=None):
        super(VCMessageBox, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle(title)
        self.setIconPixmap(QPixmap(':images/warning.png'))
        color = '#C681D5' if self.parent.theme == 'dark' else '#642C68'
        self.setText('''
            <style>
                h2 {{
                    color: {color};
                    font-family: "Futura LT", sans-serif;
                    font-weight: normal;
                }}
            </style>
            <table border="0" cellpadding="6" cellspacing="0" width="{width}">
                <tr>
                    <td><h2>{heading}</h2></td>
                </tr>
                <tr>
                    <td>{text}</td>
                </tr>
            </table>'''.format(**locals()))
        if buttons is not None:
            self.setStandardButtons(buttons)


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
        self.setWindowTitle('Cannot add media')
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
                h1 {{
                    text-align: center;
                    color: {0};
                    font-family: "Futura LT", sans-serif;
                    font-weight: normal;
                }}
                p {{
                    font-family: "Noto Sans", sans-serif;
                    color: {1};
                }}
            </style>
            <h1>Invalid media files detected</h1>
            <p>
                One or more media files were rejected and are listed below. Clicking on the filenames will reveal
                information about the error, explaining why it could not be added. 
            </p>'''.format(self.headingcolor, self.pencolor))

    # noinspection PyUnusedLocal
    @pyqtSlot(int)
    def selectItem(self, index: int) -> None:
        self.toolbox.adjustSize()
        self.adjustSize()

    def parseErrors(self) -> None:
        for file, error in self.errors:
            if not len(error):
                error = '<div align="center">Invalid media file.<br/><br/>This is not a media file or the file ' \
                        'may be corrupted.</div>'
            errorLabel = QLabel(error, self)
            index = self.toolbox.addItem(errorLabel, os.path.basename(file))
            self.toolbox.setItemToolTip(index, file)

    def setDetailedMessage(self, msg: str) -> None:
        msg = '''
        <style>
            h1 {{
                text-align: center;
                color: {0};
                font-family: "Futura LT", sans-serif;
                font-weight: normal;
            }}
            p {{
                font-family: "Noto Sans", sans-serif;
                font-weight: 300;
                color: {1};
            }}
        </style>
        <h1>Help :: Adding media files</h1>
        {2}'''.format(self.headingcolor, self.pencolor, msg)
        helpbutton = self.buttons.addButton('Help', QDialogButtonBox.ResetRole)
        helpbutton.setCursor(Qt.PointingHandCursor)
        helpbutton.clicked.connect(lambda: QMessageBox.information(self, 'Help :: Adding Media Files', msg,
                                                                   QMessageBox.Ok))
