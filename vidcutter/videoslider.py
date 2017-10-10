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
import math
import os
import sys

from PyQt5.QtCore import QEvent, QObject, QRect, QSize, QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QKeyEvent, QMouseEvent, QPaintEvent, QPainter, QPalette, QPen, QTransform, QWheelEvent
from PyQt5.QtWidgets import (qApp, QGraphicsEffect, QHBoxLayout, QLabel, QLayout, QSizePolicy, QSlider, QStackedLayout,
                             QStackedWidget, QStyle, QStyleOptionSlider, QStylePainter, QWidget)

from vidcutter.libs.videoservice import VideoService


class VideoSlider(QSlider):
    def __init__(self, parent=None):
        super(VideoSlider, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.theme = self.parent.theme
        self._styles = '''QSlider:horizontal { margin: 16px 8px 32px; height: %ipx; }
        QSlider::groove:horizontal {
            border: 1px ridge #444;
            height: %ipx;
            %s
            margin: 0;
        }
        QSlider::sub-page:horizontal {
            border: none;
            background: %s;
            height: %ipx;
            position: absolute;
            left: 0;
            right: 0;
            margin: 0;
            margin-left: %s;
        }
        QSlider::add-page:horizontal{
            border: none;
            background: transparent;
        }
        QSlider::handle:horizontal {
            border: none;
            border-radius: 0;
            background: transparent url(:images/%s) no-repeat top center;
            width: 15px;
            height: %spx;
            margin: -12px -8px -20px;
        }'''
        self._regions = list()
        self._regionHeight = 32
        self._regionSelected = -1
        self._cutStarted = False
        self.showThumbs = True
        self.thumbnailsOn = False
        self.offset = 8
        self.setOrientation(Qt.Horizontal)
        self.setObjectName('videoslider')
        self.setAttribute(Qt.WA_Hover, True)
        self.setStatusTip('Set clip start and end points')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRange(0, 0)
        self.setSingleStep(1)
        self.setTickInterval(100000)
        self.setMouseTracking(True)
        self.setTracking(True)
        self.setTickPosition(QSlider.TicksBelow)
        self.setFocus()
        self.restrictValue = 0
        self.valueChanged.connect(self.restrictMove)
        self.installEventFilter(self)

    def initStyle(self) -> None:
        bground = 'rgba(200, 213, 236, 0.85)' if self._cutStarted else 'transparent'
        height = 60
        handle = 'handle.png'
        handleHeight = 85
        margin = 0
        self._regionHeight = 32
        if self.thumbnailsOn:
            timeline = 'background: transparent url(:images/filmstrip-thumbs.png) repeat-x left;'
        else:
            if self.parent.thumbnailsButton.isChecked():
                timeline = 'background: #000 url(:images/filmstrip.png) repeat-x left;'
            else:
                timeline = 'background: #000 url(:images/filmstrip-nothumbs.png) repeat-x left;'
                handleHeight = 42
            height = 15 if not self.parent.thumbnailsButton.isChecked() else height
            handle = 'handle-nothumbs.png' if not self.parent.thumbnailsButton.isChecked() else handle
            self._regionHeight = 32 if self.parent.thumbnailsButton.isChecked() else 12
        if self._cutStarted:
            _file, _ext = os.path.splitext(handle)
            handle = '%s-select%s' % (_file, _ext)
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            control = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            margin = '%ipx' % control.x()
        self.setStyleSheet(self._styles % (height, height, timeline, bground, height + 2, margin, handle, handleHeight))

    def setRestrictValue(self, value: int, force: bool = False) -> None:
        self.restrictValue = value
        if value > 0 or force:
            self._cutStarted = True
        else:
            self._cutStarted = False
        self.initStyle()

    @pyqtSlot(int)
    def restrictMove(self, value: int) -> None:
        if value < self.restrictValue:
            self.setSliderPosition(self.restrictValue)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QStylePainter(self)
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        font = painter.font()
        font.setPixelSize(11)
        painter.setFont(font)
        if self.tickPosition() != QSlider.NoTicks:
            x = 8
            for i in range(self.minimum(), self.width(), 8):
                if i % 5 == 0:
                    h = 18
                    w = 1
                    z = 13
                else:
                    h = 8
                    w = 1
                    z = 23
                tickcolor = QColor('#8F8F8F' if self.theme == 'dark' else '#888')
                pen = QPen(tickcolor)
                pen.setWidthF(w)
                painter.setPen(pen)
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksAbove):
                    y = self.rect().top() + z
                    painter.drawLine(x, y, x, y + h)
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksBelow):
                    y = self.rect().bottom() - z
                    painter.drawLine(x, y, x, y - h)
                    if self.parent.mediaAvailable and i % 10 == 0 and (x + 4 + 50) < self.width():
                        painter.setPen(Qt.white if self.theme == 'dark' else QColor('#444'))
                        timecode = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), x - self.offset,
                                                                  self.width() - (self.offset * 2))
                        timecode = self.parent.delta2QTime(timecode).toString(self.parent.runtimeformat)
                        painter.drawText(x + 4, y + 6, timecode)
                if x + 30 > self.width():
                    break
                x += 15
        opt.subControls = QStyle.SC_SliderGroove
        painter.drawComplexControl(QStyle.CC_Slider, opt)
        for rect in self._regions:
            rect.setY(int((self.height() - self._regionHeight) / 2) - 8)
            rect.setHeight(self._regionHeight)
            if self._regions.index(rect) == self._regionSelected:
                brushcolor = QColor(150, 190, 78, 185)
            else:
                brushcolor = QColor(237, 242, 255, 185)
            painter.setBrush(brushcolor)
            painter.setPen(QColor(255, 255, 255, 170))
            painter.drawRect(rect)
        opt.subControls = QStyle.SC_SliderHandle
        painter.drawComplexControl(QStyle.CC_Slider, opt)

    def addRegion(self, start: int, end: int) -> None:
        x = self.style().sliderPositionFromValue(self.minimum(), self.maximum(), start - self.offset,
                                                 self.width() - (self.offset * 2))
        y = int((self.height() - self._regionHeight) / 2)
        width = self.style().sliderPositionFromValue(self.minimum(), self.maximum(), end - self.offset,
                                                     self.width() - (self.offset * 2)) - x
        height = self._regionHeight
        rect = QRect(x + self.offset, y - 8, width, height)
        self._regions.append(rect)
        self.update()

    def switchRegions(self, index1: int, index2: int) -> None:
        reg = self._regions.pop(index1)
        self._regions.insert(index2, reg)
        self.update()

    def selectRegion(self, clipindex: int) -> None:
        self._regionSelected = clipindex
        self.update()

    def clearRegions(self) -> None:
        self._regions.clear()
        self._regionSelected = -1
        self.update()

    def initThumbs(self) -> None:
        framesize = self.parent.videoService.framesize()
        thumbsize = QSize(VideoService.ThumbSize.TIMELINE.value.height() * (framesize.width() / framesize.height()),
                          VideoService.ThumbSize.TIMELINE.value.height())
        positions = list()
        thumbs = int(math.ceil((self.width() - (self.offset * 2)) / thumbsize.width()))
        for pos in range(thumbs):
            val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(),
                                                 (thumbsize.width() * pos) - self.offset,
                                                 self.width() - (self.offset * 2))
            positions.append(val)
        positions[0] = 1000
        frametimes = list()
        [frametimes.append(self.parent.delta2QTime(msec).toString(self.parent.timeformat)) for msec in positions]

        class ThumbWorker(QObject):
            completed = pyqtSignal(list)

            def __init__(self, media: str, times: list, size: QSize):
                super(ThumbWorker, self).__init__()
                self.media = media
                self.times = times
                self.size = size

            def generate(self):
                frames = list()
                for frame in self.times:
                    frames.append(VideoService.captureFrame(self.media, frame, self.size))
                self.completed.emit(frames)

        self.thumbsThread = QThread(self)
        self.thumbsWorker = ThumbWorker(self.parent.currentMedia, frametimes, thumbsize)
        self.thumbsWorker.moveToThread(self.thumbsThread)
        self.thumbsThread.started.connect(self.parent.sliderWidget.setLoader)
        self.thumbsThread.started.connect(self.thumbsWorker.generate)
        self.thumbsThread.finished.connect(self.thumbsThread.deleteLater, Qt.DirectConnection)
        self.thumbsWorker.completed.connect(self.buildTimeline)
        self.thumbsWorker.completed.connect(self.thumbsWorker.deleteLater, Qt.DirectConnection)
        self.thumbsWorker.completed.connect(self.thumbsThread.quit, Qt.DirectConnection)
        self.thumbsThread.start()

    @pyqtSlot(list)
    def buildTimeline(self, thumbs: list) -> None:
        layout = QHBoxLayout()
        layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 16, 0, 0)
        for thumb in thumbs:
            label = QLabel()
            label.setStyleSheet('padding: 0; margin: 0;')
            label.setFixedSize(thumb.size())
            label.setPixmap(thumb)
            layout.addWidget(label)
        thumbnails = QWidget(self)
        thumbnails.setLayout(layout)
        self.removeThumbs()
        self.parent.sliderWidget.addWidget(thumbnails)
        self.thumbnailsOn = True
        self.initStyle()
        self.parent.sliderWidget.setLoader(False)
        if self.parent.newproject:
            self.parent.renderClipIndex()
            self.parent.newproject = False

    def removeThumbs(self) -> None:
        if self.parent.sliderWidget.count() == 3:
            thumbWidget = self.parent.sliderWidget.widget(2)
            self.parent.sliderWidget.removeWidget(thumbWidget)
            thumbWidget.deleteLater()
            self.setObjectName('nothumbs')
            self.thumbnailsOn = False

    def errorHandler(self, error: str) -> None:
        self.logger.error(error)
        sys.stderr.write(error)

    def reloadThumbs(self) -> None:
        if self.parent.mediaAvailable and self.parent.thumbnailsButton.isChecked():
            if self.thumbnailsOn:
                if self.parent.sliderWidget.count() == 2:
                    self.parent.sliderWidget.widget(1).hide()
                self.thumbnailsOn = False
            self.initStyle()
            self.initThumbs()
            self.parent.renderClipIndex()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.parent.mediaAvailable:
            if event.angleDelta().y() > 0:
                self.parent.mpvWidget.frameBackStep()
            else:
                self.parent.mpvWidget.frameStep()
            event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        qApp.sendEvent(self.parent, event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        handle = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        if handle.x() <= event.pos().x() <= (handle.x() + handle.width()):
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()
        super(VideoSlider, self).mouseMoveEvent(event)

    def eventFilter(self, obj: QObject, event: QMouseEvent) -> bool:
        if event.type() == QEvent.MouseButtonRelease:
            if self.parent.mediaAvailable and self.isEnabled():
                newpos = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x() - self.offset,
                                                        self.width() - (self.offset * 2))
                self.setValue(newpos)
                self.parent.setPosition(newpos)
                self.parent.parent.mousePressEvent(event)
        return super(VideoSlider, self).eventFilter(obj, event)


class VideoSliderWidget(QStackedWidget):
    def __init__(self, parent, slider: VideoSlider):
        super(VideoSliderWidget, self).__init__(parent)
        self.parent = parent
        self.slider = slider
        self.loaderEffect = self.LoaderEffect()
        self.loaderEffect.setEnabled(False)
        self.setGraphicsEffect(self.loaderEffect)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout().setStackingMode(QStackedLayout.StackAll)
        self.addWidget(self.slider)
        spacerlabel1 = QLabel(self)
        spacerlabel1.setFixedWidth(15)
        spacerlabel1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        spacerlabel1.setStyleSheet('background: {};'.format(self.palette().color(QPalette.Window).name()))
        spacerlabel2 = QLabel(self)
        spacerlabel2.setFixedWidth(15)
        spacerlabel2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        spacerlabel2.setStyleSheet('background: {};'.format(self.palette().color(QPalette.Window).name()))
        trimlayout = QHBoxLayout()
        trimlayout.addWidget(spacerlabel1, 0, Qt.AlignLeft)
        trimlayout.addStretch()
        trimlayout.addWidget(spacerlabel2, 0, Qt.AlignRight)
        trimwidget = QWidget(self)
        trimwidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        trimwidget.setContentsMargins(-15, 6, -15, 0)
        trimwidget.setLayout(trimlayout)
        self.addWidget(trimwidget)

    def setLoader(self, enabled: bool=True) -> None:
        if hasattr(self.parent, 'toolbar') and self.parent.mediaAvailable:
            self.parent.toolbar.setEnabled(not enabled)
        self.slider.setEnabled(not enabled)
        self.loaderEffect.setEnabled(enabled)

    class LoaderEffect(QGraphicsEffect):
        def draw(self, painter: QPainter) -> None:
            if self.sourceIsPixmap():
                pixmap, offset = self.sourcePixmap(Qt.LogicalCoordinates, QGraphicsEffect.PadToEffectiveBoundingRect)
            else:
                pixmap, offset = self.sourcePixmap(Qt.DeviceCoordinates, QGraphicsEffect.PadToEffectiveBoundingRect)
                painter.setWorldTransform(QTransform())
            painter.setBrush(Qt.black)
            painter.drawRect(pixmap.rect())
            painter.setOpacity(0.2)
            painter.drawPixmap(offset, pixmap)
