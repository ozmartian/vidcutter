#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QSlider, QStyleFactory, QStyleOptionSlider, QToolTip, qApp


class VideoSlider(QSlider):
    def __init__(self, *arg, **kwargs):
        super(QSlider, self).__init__(*arg, **kwargs)
        self.setStyle(QStyleFactory.create('Windows'))
        self.setOrientation(Qt.Horizontal)
        self.setObjectName('VideoSlider')
        self.setStatusTip('Set clip start and end points')
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimum(0)
        self.setMaximum(0)
        self.setSingleStep(1)
        self.setTracking(True)
        self.setFocus()
        self.setCutMode(False)
        self.restrictValue = 0
        self.style = qApp.style()
        self.opt = QStyleOptionSlider()
        self.valueChanged.connect(self.restrictMove)

    def setSliderColor(self):
        self.sliderQSS = '''QSlider:horizontal { margin: 15px 5px 10px; }
QSlider::groove:horizontal {
    border: 1px inset #999;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %s, stop:1 %s);
    height: 8px;
    position: absolute;
    left: 2px;
    right: 2px;
    margin: -2px 0;
}
QSlider::sub-page:horizontal {
    border: 1px solid #999;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %s, stop:1 %s);
    height: 8px;
    position: absolute;
    left: 2px;
    right: 2px;
    margin: -2px 0;
}
QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %s, stop:1 %s);
    border: 1px solid #444;
    width: 10px;
    height: 12px;
    margin: -12px -2px;
    border-radius: 2px;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %s, stop:1 %s);
}''' % (self.grooveBack1, self.grooveBack2, self.subBack1, self.subBack2,
        self.handleBack1, self.handleBack2, self.handleHoverBack1, self.handleHoverBack2)
        self.setStyleSheet(self.sliderQSS)

    def setRestrictValue(self, value):
        self.restrictValue = value

    def restrictMove(self, value):
        if value < self.restrictValue:
            self.setSliderPosition(self.restrictValue)
        else:
            self.initStyleOption(self.opt)
            rectHandle = self.style.subControlRect(self.style.CC_Slider, self.opt, self.style.SC_SliderHandle)
            posLocal = rectHandle.topLeft() + QPoint(20, -20)
            posGlobal = self.mapToGlobal(posLocal)
            timerValue = self.parentWidget().timeCounter.text().split(' / ')[0]
            QToolTip.showText(posGlobal, timerValue, self)

    def setCutMode(self, flag):
        if flag:
            self.grooveBack1 = '#FFF'
            self.grooveBack2 = '#6A4572'
            self.subBack1 = '#FFF'
            self.subBack2 = '#FFF'
            self.handleBack1 = '#666666'
            self.handleBack2 = '#666666'
            self.handleHoverBack1 = '#CCC'
            self.handleHoverBack2 = '#999'
        else:
            self.grooveBack1 = '#FFF'
            self.grooveBack2 = '#FFF'
            self.subBack1 = '#FFF'
            self.subBack2 = '#6A4572'
            self.handleBack1 = '#666666'
            self.handleBack2 = '#666666'
            self.handleHoverBack1 = '#CCC'
            self.handleHoverBack2 = '#999'
        self.setSliderColor()

    def wheelEvent(self, event):
        qApp.sendEvent(self.parentWidget(), event)

    def keyPressEvent(self, event):
        qApp.sendEvent(self.parentWidget(), event)
