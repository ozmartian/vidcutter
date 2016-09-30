#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QKeyEvent, QPaintEvent, QWheelEvent
from PyQt5.QtWidgets import QSlider, QStyle, QStyleFactory, QStyleOptionSlider, QStylePainter, QToolTip, qApp


# from QxtSpanSlider import QxtSpanSlider

class VideoSlider(QSlider):
    def __init__(self, *arg, **kwargs):
        super(VideoSlider, self).__init__(*arg, **kwargs)
        self.setStyle(QStyleFactory.create('Windows'))
        self.setOrientation(Qt.Horizontal)
        self.setObjectName('VideoSlider')
        self.setStatusTip('Set clip start and end points')
        self.setCursor(Qt.ClosedHandCursor)
        self.setRange(0, 0)
        self.setSingleStep(1)
        self.setTracking(True)
        self.setTickInterval(100000)
        self.setTickPosition(QSlider.TicksAbove)
        self.setFocus()
        self.setCutMode(False)
        self.restrictValue = 0
        self.style = qApp.style()
        self.opt = QStyleOptionSlider()
        self.posLocal, self.posGlobal = 0, 0
        self.valueChanged.connect(self.restrictMove)

    def setSliderColor(self) -> None:
        self.sliderQSS = '''QSlider:horizontal { margin: 20px 0 10px; }
QSlider::groove:horizontal {
    border: 1px inset #999;
    /* background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FEFEFE, stop:1 #FEFEFE); */
    background: url(:images/filmstrip.png) repeat-x;
    height: 14px;
    position: absolute;
    left: 0;
    right: 0;
    margin: 0 0;
}
QSlider::sub-page:horizontal {
    border: 1px inset #999;
    /* background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #CCC, stop:1 #666); */
    background: rgba(255, 255, 255, 0.6);
    height: 14px;
    position: absolute;
    left: 0;
    right: 0;
    margin: 0 0;
}
QSlider::handle:horizontal {
    border: none;
    background: url(:images/slider-handle.png) no-repeat top center;
    width: 20px;
    height: 47px;
    margin: -21px 0;
}'''
        self.setStyleSheet(self.sliderQSS)

    def setValueNoSignal(self, value: int) -> None:
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)

    def setRestrictValue(self, value: int) -> None:
        self.restrictValue = value

    def restrictMove(self, value: int) -> None:
        if value < self.restrictValue:
            self.setSliderPosition(self.restrictValue)
        else:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            rectHandle = self.style.subControlRect(self.style.CC_Slider, opt, self.style.SC_SliderHandle, self)
            posLocal = rectHandle.topLeft() + QPoint(20, -20)
            posGlobal = self.mapToGlobal(posLocal)
            timerValue = self.parentWidget().timeCounter.text().split(' / ')[0]
            QToolTip.showText(posGlobal, timerValue, self)

    def setCutMode(self, flag: bool) -> None:
        # if flag:
        #     self.grooveBack1 = '#6A4572'
        #     self.grooveBack2 = '#FFF'
        #     self.subBack1 = '#FFF'
        #     self.subBack2 = '#FFF'
        # else:
        #     self.grooveBack1 = '#FEFEFE'
        #     self.grooveBack2 = '#FEFEFE'
        #     self.subBack1 = '#CCC'
        #     self.subBack2 = '#666'
        self.setSliderColor()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QStylePainter(self)
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        handle = self.style.subControlRect(self.style.CC_Slider, opt, self.style.SC_SliderHandle, self)
        interval = self.tickInterval()
        if interval == 0:
            interval = self.pageStep()
        if self.tickPosition() != QSlider.NoTicks:
            for i in range(self.minimum(), self.maximum(), interval):
                x = round((((i - self.minimum()) / (self.maximum() - self.minimum()))
                           * (self.width() - handle.width()) + (handle.width() / 2.0))) - 1
                if i % 500000 == 0:
                    h = 12
                    z = 8
                else:
                    h = 6
                    z = 14
                painter.setPen(QColor('#A5A294'))
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksAbove):
                    y = self.rect().top() + z
                    painter.drawLine(x, y, x, y + h)
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksBelow):
                    y = self.rect().bottom() - z
                    painter.drawLine(x, y, x, y - h)
        opt.subControls = QStyle.SC_SliderGroove
        painter.drawComplexControl(QStyle.CC_Slider, opt)
        opt.subControls = QStyle.SC_SliderHandle
        painter.drawComplexControl(QStyle.CC_Slider, opt)

    def wheelEvent(self, event: QWheelEvent) -> None:
        qApp.sendEvent(self.parentWidget(), event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        qApp.sendEvent(self.parentWidget(), event)
