#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import operator
from enum import Enum

from PyQt5.QtCore import pyqtSlot, QPointF, Qt, QRectF
from PyQt5.QtGui import (QPalette, QConicalGradient, QGradient, QRadialGradient, QFontMetricsF, QFont, QPainter, QPen,
                         QPainterPath, QImage, QPaintEvent)
from PyQt5.QtWidgets import QWidget


class QRoundProgressBar(QWidget):
    PositionLeft = 180
    PositionTop = 90
    PositionRight = 0
    PositionBottom = -90

    # CONSTRUCTOR ---------------------------------------------------

    def __init__(self, parent=None):
        super(QRoundProgressBar, self).__init__(parent)
        self.m_min = 0
        self.m_max = 100
        self.m_value = 25
        self.m_nullPosition = QRoundProgressBar.PositionTop
        self.m_barStyle = self.BarStyle.DONUT
        self.m_outlinePenWidth = 1
        self.m_dataPenWidth = 1
        self.m_rebuildBrush = False
        self.m_format = '%p%'
        self.m_decimals = 1
        self.m_updateFlags = self.UpdateFlags.PERCENT
        self.m_gradientData = None

    # ENUMS ---------------------------------------------------------

    class BarStyle(Enum):
        DONUT = 0,
        PIE = 1,
        LINE = 2,
        EXPAND = 3

    class UpdateFlags(Enum):
        VALUE = 0,
        PERCENT = 1,
        MAX = 2

    # GETTERS -------------------------------------------------------

    def minimum(self):
        return self.m_min

    def maximum(self):
        return self.m_max

    # SETTERS -------------------------------------------------------

    def setNullPosition(self, position: float):
        if position != self.m_nullPosition:
            self.m_nullPosition = position
            self.m_rebuildBrush = True
            self.update()

    def setBarStyle(self, style: BarStyle):
        if style != self.m_barStyle:
            self.m_barStyle = style
            self.m_rebuildBrush = True
            self.update()

    def setOutlinePenWidth(self, width: float):
        if width != self.m_outlinePenWidth:
            self.m_outlinePenWidth = width
            self.update()

    def setDataPenWidth(self, width: float):
        if width != self.m_dataPenWidth:
            self.m_dataPenWidth = width
            self.update()

    def setDataColors(self, stopPoints: list):
        if stopPoints != self.m_gradientData:
            self.m_gradientData = stopPoints
            self.m_rebuildBrush = True
            self.update()

    def setFormat(self, val: str):
        if val != self.m_format:
            self.m_format = val
            self.valueFormatChanged()

    def resetFormat(self):
        self.m_format = None
        self.valueFormatChanged()

    def setDecimals(self, count: int):
        if count >= 0 and count != self.m_decimals:
            self.m_decimals = count
            self.valueFormatChanged()

    # SLOTS ---------------------------------------------------------

    @pyqtSlot(float, float)
    def setRange(self, minval: float, maxval: float):
        self.m_min = minval
        self.m_max = maxval
        if self.m_max < self.m_min:
            self.m_min = maxval
            self.m_max = minval
        if self.m_value < self.m_min:
            self.m_value = self.m_min
        elif self.m_value > self.m_max:
            self.m_value = self.m_max
        self.m_rebuildBrush = True
        self.update()

    @pyqtSlot(float)
    def setMinimum(self, val: float):
        self.setRange(val, self.m_max)

    @pyqtSlot(float)
    def setMaximum(self, val: float):
        self.setRange(self.m_min, val)

    @pyqtSlot(int)
    def setValue(self, val: int):
        if self.m_value != val:
            if val < self.m_min:
                self.m_value = self.m_min
            elif val > self.m_max:
                self.m_value = self.m_max
            else:
                self.m_value = val
            self.update()

    # PAINTING ------------------------------------------------------

    def paintEvent(self, event: QPaintEvent):
        outerRadius = min(self.width(), self.height())
        baseRect = QRectF(1, 1, outerRadius - 2, outerRadius - 2)
        buffer = QImage(outerRadius, outerRadius, QImage.Format_ARGB32_Premultiplied)
        p = QPainter(buffer)
        p.setRenderHint(QPainter.Antialiasing)
        self.rebuildDataBrushIfNeeded()
        self.drawBackground(p, buffer.rect())
        self.drawBase(p, baseRect)
        if self.m_value > 0:
            delta = (self.m_max - self.m_min) / (self.m_value - self.m_min)
        else:
            delta = 0
        self.drawValue(p, baseRect, self.m_value, delta)
        innerRect, innerRadius = self.calculateInnerRect(outerRadius)
        self.drawInnerBackground(p, innerRect)
        self.drawText(p, innerRect, innerRadius, self.m_value)
        p.end()
        painter = QPainter(self)
        painter.fillRect(baseRect, self.palette().window())
        painter.drawImage(0, 0, buffer)

    def drawBackground(self, p: QPainter, baseRect: QRectF):
        p.fillRect(baseRect, self.palette().window())

    def drawBase(self, p: QPainter, baseRect: QRectF):
        if self.m_barStyle == self.BarStyle.DONUT:
            p.setPen(QPen(self.palette().shadow().color(), self.m_outlinePenWidth))
            p.setBrush(self.palette().base())
            p.drawEllipse(baseRect)
        elif self.m_barStyle == self.BarStyle.LINE:
            p.setPen(QPen(self.palette().base().color(), self.m_outlinePenWidth))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
                                            -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2))
        elif self.m_barStyle in (self.BarStyle.PIE, self.BarStyle.EXPAND):
            p.setPen(QPen(self.palette().base().color(), self.m_outlinePenWidth))
            p.setBrush(self.palette().base())
            p.drawEllipse(baseRect)

    def drawValue(self, p: QPainter, baseRect: QRectF, value: float, delta: float):
        if value == self.m_min:
            return
        if self.m_barStyle == self.BarStyle.EXPAND:
            p.setBrush(self.palette().highlight())
            p.setPen(QPen(self.palette().shadow().color(), self.m_dataPenWidth))
            radius = (baseRect.height() / 2) / delta
            p.drawEllipse(baseRect.center(), radius, radius)
            return
        if self.m_barStyle == self.BarStyle.LINE:
            p.setPen(QPen(self.palette().highlight().color(), self.m_dataPenWidth))
            p.setBrush(Qt.NoBrush)
            if value == self.m_max:
                p.drawEllipse(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
                                                -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2))
            else:
                arcLength = 360 / delta
                p.drawArc(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
                                            -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2),
                          int(self.m_nullPosition * 16),
                          int(-arcLength * 16))
            return
        dataPath = QPainterPath()
        dataPath.setFillRule(Qt.WindingFill)
        if value == self.m_max:
            dataPath.addEllipse(baseRect)
        else:
            arcLength = 360 / delta
            dataPath.moveTo(baseRect.center())
            dataPath.arcTo(baseRect, self.m_nullPosition, -arcLength)
            dataPath.lineTo(baseRect.center())
        p.setBrush(self.palette().highlight())
        p.setPen(QPen(self.palette().shadow().color(), self.m_dataPenWidth))
        p.drawPath(dataPath)

    def calculateInnerRect(self, outerRadius: float):
        if self.m_barStyle in (self.BarStyle.LINE, self.BarStyle.EXPAND):
            innerRadius = outerRadius - self.m_outlinePenWidth
        else:
            innerRadius = outerRadius * 0.75
        delta = (outerRadius - innerRadius) / 2
        innerRect = QRectF(delta, delta, innerRadius, innerRadius)
        return innerRect, innerRadius

    def drawInnerBackground(self, p: QPainter, innerRect: QRectF):
        if self.m_barStyle == self.BarStyle.DONUT:
            p.setBrush(self.palette().alternateBase())
            p.drawEllipse(innerRect)

    def drawText(self, p: QPainter, innerRect: QRectF, innerRadius: float, value: float):
        if not self.m_format:
            return
        f = QFont(self.font())
        f.setPixelSize(10)
        fm = QFontMetricsF(f)
        maxWidth = fm.width(self.valueToText(self.m_max))
        delta = innerRadius / maxWidth
        fontSize = f.pixelSize() * delta * 0.75
        f.setPixelSize(int(fontSize))
        p.setFont(f)
        textRect = QRectF(innerRect)
        p.setPen(self.palette().text().color())
        p.drawText(textRect, Qt.AlignCenter, self.valueToText(value))

    def valueToText(self, value: float):
        textToDraw = self.m_format
        if self.m_updateFlags == self.UpdateFlags.VALUE:
            textToDraw = textToDraw.replace('%v', str(round(value, self.m_decimals)))
        if self.m_updateFlags == self.UpdateFlags.PERCENT:
            procent = (value - self.m_min) / (self.m_max - self.m_min) * 100
            textToDraw = textToDraw.replace('%p', str(round(procent, self.m_decimals)))
        if self.m_updateFlags == self.UpdateFlags.MAX:
            textToDraw = textToDraw.replace('%m', str(round(self.m_max - self.m_min + 1, self.m_decimals)))
        return textToDraw

    def valueFormatChanged(self):
        if operator.contains(self.m_format, '%v'):
            self.m_updateFlags = self.UpdateFlags.VALUE
        if operator.contains(self.m_format, '%p'):
            self.m_updateFlags = self.UpdateFlags.PERCENT
        if operator.contains(self.m_format, '%m'):
            self.m_updateFlags = self.UpdateFlags.MAX
        self.update()

    def rebuildDataBrushIfNeeded(self):
        if not self.m_rebuildBrush or not self.m_gradientData or self.m_barStyle == self.BarStyle.LINE:
            return
        self.m_rebuildBrush = False
        p = self.palette()
        if self.m_barStyle == self.BarStyle.EXPAND:
            dataBrush = QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
            dataBrush.setCoordinateMode(QGradient.StretchToDeviceMode)
            for i in range(0, len(self.m_gradientData)):
                dataBrush.setColorAt(self.m_gradientData[i][0], self.m_gradientData[i][1])
            p.setBrush(QPalette.Highlight, dataBrush)
        else:
            dataBrush = QConicalGradient(QPointF(0.5, 0.5), self.m_nullPosition)
            dataBrush.setCoordinateMode(QGradient.StretchToDeviceMode)
            for i in range(0, len(self.m_gradientData)):
                dataBrush.setColorAt(1 - self.m_gradientData[i][0], self.m_gradientData[i][1])
            p.setBrush(QPalette.Highlight, dataBrush)
        self.setPalette(p)
