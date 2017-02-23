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

import logging
import sys

from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSlot
from PyQt5.QtGui import (QBrush, QColor, QCursor, QKeyEvent, QMouseEvent, QPaintEvent, QPainterPath, QPen, QPixmap,
                         QWheelEvent)
from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider, QStylePainter, qApp


class VideoSlider(QSlider):
    def __init__(self, *arg, **kwargs):
        super(VideoSlider, self).__init__(*arg, **kwargs)
        self._regions = list()
        self._regionHeight = 12
        self._regionSelected = -1
        self.logger = logging.getLogger(__name__)
        self.setOrientation(Qt.Horizontal)
        self.setObjectName('videoslider')
        self.setAttribute(Qt.WA_Hover, True)
        self.setStatusTip('Set clip start and end points')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRange(0, 0)
        self.setSingleStep(1)
        self.setMouseTracking(True)
        self.setTracking(True)
        self.setTickPosition(QSlider.TicksAbove)
        self.slider_cursor = QCursor(QPixmap(':/images/slider-cursor.png', 'PNG'))\
            if sys.platform.startswith('linux') else Qt.SplitHCursor
        self.setFocus()
        self.initStyle()
        self.restrictValue = 0
        self.valueChanged.connect(self.restrictMove)
        self.installEventFilter(self)

    def initStyle(self, selected: bool = False, margin: str = '0') -> None:
        bground = 'transparent'
        if selected:
            bground = 'rgba(200, 213, 236, 0.85)'
        self.setStyleSheet(self.getStyleSheet(bground, margin))

    def setRestrictValue(self, value: int, force: bool = False) -> None:
        self.restrictValue = value
        if value > 0 or force:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            handle = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            self.initStyle(True, '%ipx' % (handle.x() + 5))
        else:
            self.initStyle()

    @pyqtSlot(int)
    def restrictMove(self, value: int) -> None:
        if value < self.restrictValue:
            self.setSliderPosition(self.restrictValue)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QStylePainter(self)
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        if self.tickPosition() != QSlider.NoTicks:
            x = 4
            for i in range(self.minimum(), self.width(), x):
                if i % 5 == 0:
                    h = 18
                    w = 1
                    z = 8
                else:
                    h = 7
                    w = 0.8
                    z = 15
                pen = QPen(QColor('#444'))
                pen.setWidthF(w)
                painter.setPen(pen)
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksAbove):
                    y = self.rect().top() + z
                    painter.drawLine(x, y, x, y + h)
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksBelow):
                    y = self.rect().bottom() - z
                    painter.drawLine(x, y, x, y - h)
                x += 10
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
        path.addRect(x, y + 3, width, height)
        self._regions.append(path)
        self.update()

    def switchRegions(self, index1: int, index2: int) -> None:
        reg = self._regions.pop(index1)
        self._regions.insert(index2, reg)
        self.update()

    def highlightRegion(self, clipindex: int):
        self._regionSelected = clipindex
        self.update()

    def clearRegions(self) -> None:
        self._regions.clear()
        self._regionSelected = -1
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        qApp.sendEvent(self.parentWidget(), event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        qApp.sendEvent(self.parentWidget(), event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        handle = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        if handle.x() <= event.pos().x() <= (handle.x() + handle.width()):
            self.setCursor(self.slider_cursor)
        else:
            self.unsetCursor()
        super(VideoSlider, self).mouseMoveEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonRelease:
            if self.parentWidget().mediaAvailable:
                self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width()))
                self.parentWidget().setPosition(self.sliderPosition())
        return super(VideoSlider, self).eventFilter(obj, event)

    def getStyleSheet(self, bground: str, margin: str) -> str:
        return '''QSlider:horizontal { margin: 25px 0 18px; }
QSlider::groove:horizontal {
    border: none;
    height: 32px;
    background: #333 url(:images/filmstrip.png) repeat-x;
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
    width: 20px;
    height: 58px;
    margin: -15px -8px;
}''' % (bground, margin)
