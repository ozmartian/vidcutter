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
import logging

from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSlot
from PyQt5.QtGui import (QColor, QKeyEvent, QMouseEvent, QPaintEvent, QPainter, QPainterPath, QPen, QResizeEvent,
                         QTransform, QWheelEvent)
from PyQt5.QtWidgets import (qApp, QGraphicsEffect, QHBoxLayout, QLabel, QSlider, QStyle, QStyleOptionSlider,
                             QStackedWidget, QStylePainter, QWidget, QSizePolicy, QStackedLayout)

from vidcutter.videothreads import TimelineThumbsThread
from vidcutter.libs.videoservice import VideoService


class VideoSlider(QSlider):
    def __init__(self, parent=None, *arg, **kwargs):
        super(VideoSlider, self).__init__(parent, *arg, **kwargs)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.theme = self.parent.theme
        self._styles = '''QSlider:horizontal { margin: 16px 4px 22px; height: 40px; }
        QSlider::groove:horizontal {
            border-bottom: 1px solid #444;
            border-top: 1px solid #444;
            height: 38px;
            background: %s url(:images/%s.png) repeat-x left;
            position: absolute;
            left: 4px;
            right: 4px;
            margin: 0;
        }
        QSlider::sub-page:horizontal {
            border: none;
            background: %s;
            height: 20px;
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
            background: url(:images/handle.png) no-repeat top center;
            width: 18px;
            height: 65px;
            margin: -12px -10px -22px;
        }'''
        self._offset = 8
        self._regions = list()
        self._regionHeight = 22
        self._regionSelected = -1
        self._showThumbs = True
        self._thumbnailsOn = False
        self.setOrientation(Qt.Horizontal)
        self.setObjectName('videoslider')
        self.setAttribute(Qt.WA_Hover, True)
        self.setStatusTip('Set clip start and end points')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRange(0, 0)
        self.setSingleStep(1)
        self.setMouseTracking(True)
        self.setTracking(True)
        self.setTickPosition(QSlider.TicksBelow)
        self.setFocus()
        self.restrictValue = 0
        self.valueChanged.connect(self.restrictMove)
        self.installEventFilter(self)

    def initStyle(self, selected: bool = False, margin: str = '0') -> None:
        bground = 'rgba(200, 213, 236, 0.85)' if selected else 'transparent'
        if self._thumbnailsOn:
            timeline_bground = 'transparent'
            timeline_image = 'filmstrip_thumbs'
        else:
            timeline_bground = '#444'
            timeline_image = 'filmstrip'
        self.setStyleSheet(self._styles % (timeline_bground, timeline_image, bground, margin))

    def setRestrictValue(self, value: int, force: bool = False) -> None:
        self.restrictValue = value
        if value > 0 or force:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            handle = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            self.initStyle(True, '%ipx' % handle.x())
        else:
            self.initStyle()

    @pyqtSlot(int)
    def restrictMove(self, value: int) -> None:
        if value < self.restrictValue:
            self.setSliderPosition(self.restrictValue)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QStylePainter(self)
        font = painter.font()
        font.setPixelSize(10)
        painter.setFont(font)
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        if self.tickPosition() != QSlider.NoTicks:
            x = self._offset
            for i in range(self.minimum(), self.width(), x):
                if i % 5 == 0:
                    h = 14
                    w = 1
                    z = 8
                else:
                    h = 5
                    w = 1
                    z = 16
                tickcolor = '#8F8F8F' if self.theme == 'dark' else '#444'
                pen = QPen(QColor(tickcolor))
                pen.setWidthF(w)
                painter.setPen(pen)
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksAbove):
                    y = self.rect().top() + z
                    painter.drawLine(x, y, x, y + h)
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksBelow):
                    y = self.rect().bottom() - z
                    painter.drawLine(x, y, x, y - h)
                    if i % 30 == 0:
                        painter.setPen(Qt.white if self.theme == 'dark' else Qt.black)
                        if self.parent.currentMedia is not None:
                            timecode = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), x - self._offset,
                                                                      self.width())
                            timecode= self.parent.delta2QTime(timecode).toString(self.parent.runtimeformat)
                        else:
                            timecode = '00:00:00'
                        painter.drawText(x + 4, y + 8, timecode)
                if x + 30 > self.width():
                    break
                x += 15
        opt.subControls = QStyle.SC_SliderGroove
        painter.drawComplexControl(QStyle.CC_Slider, opt)
        for path in self._regions:
            brushcolor = QColor(150, 190, 78, 185) if self._regions.index(path) == self._regionSelected \
                else QColor(237, 242, 255, 185)
            painter.setBrush(brushcolor)
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
        opt.subControls = QStyle.SC_SliderHandle
        painter.drawComplexControl(QStyle.CC_Slider, opt)

    def addRegion(self, start: int, end: int) -> None:
        x = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), start, self.width())
        y = (self.height() - self._regionHeight) / 2
        width = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), end, self.width()) - x
        height = self._regionHeight
        path = QPainterPath()
        path.addRect(x, y - 3, width, height)
        self._regions.append(path)
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

    def toggleThumbnails(self, checked: bool) -> None:
        if self._showThumbs and self._thumbnailsOn and not checked:
            self.parent.showText('Timeline thumbnails disabled')
            self.removeThumbs()
            self.initStyle()
        elif self.parent.currentMedia is not None:
            self.parent.showText('Timeline thumbnails enabled')
            self.timeline(self.parent.currentMedia)
        self._showThumbs = checked

    def timeline(self, source: str) -> None:
        thumbWidth = VideoService.ThumbSize.TIMELINE.value.width()
        step = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), thumbWidth, self.width() - self._offset)
        index = list(range(0, self.maximum(), step))
        frametimes = list()
        for msec in index:
            frametimes.append(self.parent.delta2QTime(msec).toString(self.parent.timeformat))
        self.parent.sliderWidget.setLoader(True)
        self.thumbsThread = TimelineThumbsThread(source, frametimes)
        self.thumbsThread.errorOccurred.connect(self.errorHandler)
        self.thumbsThread.completed.connect(self.buildTimeline)
        self.thumbsThread.start()

    @pyqtSlot(list)
    def buildTimeline(self, thumbs: list) -> None:
        layout = QHBoxLayout(spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        for thumb in thumbs:
            label = QLabel()
            label.setStyleSheet('padding: 0; margin: -5px 0 0 0; background: transparent;')
            label.setPixmap(thumb)
            layout.addWidget(label)
        thumbnails = QWidget(self)
        thumbnails.setContentsMargins(8, 16, 8, 22)
        thumbnails.setFixedSize(self.width(), self.height())
        thumbnails.setLayout(layout)
        self.removeThumbs()
        self.parent.sliderWidget.addWidget(thumbnails)
        self._thumbnailsOn = True
        self.initStyle()
        self.parent.sliderWidget.setLoader(False)

    def removeThumbs(self) -> None:
        if self.parent.sliderWidget.count() == 2:
            thumbWidget = self.parent.sliderWidget.widget(1)
            self.parent.sliderWidget.removeWidget(thumbWidget)
            thumbWidget.deleteLater()
            self._thumbnailsOn = False

    def errorHandler(self, error: str) -> None:
        self.logger.error(error)
        sys.stderr.write(error)

    def resizeEvent(self, event: QResizeEvent) -> None:
        if self._thumbnailsOn:
            if self.parent.sliderWidget.count() == 2:
                thumbWidget = self.parent.sliderWidget.widget(1)
                thumbWidget.hide()
            self.setStyleSheet(self._styles % ('#444', 'filmstrip', 'transparent', 0))
            self.timeline(self.parent.currentMedia)
        self.parent.renderTimes()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.parent.mediaAvailable:
            if event.angleDelta().y() > 0:
                self.parent.mediaPlayer.frame_back_step()
            else:
                self.parent.mediaPlayer.frame_step()
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

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonRelease:
            if self.parent.mediaAvailable:
                self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width()))
                self.parent.setPosition(self.sliderPosition())
        return super(VideoSlider, self).eventFilter(obj, event)


class VideoSliderWidget(QStackedWidget):
    def __init__(self, parent, slider: VideoSlider):
        super(VideoSliderWidget, self).__init__(parent)
        self.loaderEffect = self.LoaderEffect()
        self.loaderEffect.setEnabled(False)
        self.setGraphicsEffect(self.loaderEffect)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout().setStackingMode(QStackedLayout.StackAll)
        self.addWidget(slider)

    def setLoader(self, enabled: bool = False):
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
