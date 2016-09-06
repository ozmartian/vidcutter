#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider, QStyleFactory, qApp


class VideoSlider(QSlider):
    def __init__(self, *arg, **kwargs):
        super(QSlider, self).__init__(*arg, **kwargs)

        self.setCutMode(False)

        self.setStyle(QStyleFactory.create('Windows'))
        self.setOrientation(Qt.Horizontal)
        self.setStatusTip('Set video frame position')
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimum(0)
        self.setMaximum(0)
        self.setSingleStep(1)
        self.setTickPosition(self.TicksBothSides)
        self.setTickInterval(1)
        self.setFocus()
        self.restrictValue = 0

        self.valueChanged.connect(self.restrictMove)

    def setSliderColor(self):
        self.sliderQSS = '''QSlider:horizontal { margin: 10px 5px 6px; }
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
}''' % (self.sliderGrooveBack1, self.sliderGrooveBack2, self.sliderSubBack1, self.sliderSubBack2,
        self.sliderHandleBack1, self.sliderHandleBack2, self.sliderHandleHoverBack1, self.sliderHandleHoverBack2)
        self.setStyleSheet(self.sliderQSS)

    def setRestrictValue(self, value):
        self.restrictValue = value

    def restrictMove(self, index):
        if index < self.restrictValue:
            self.setSliderPosition(self.restrictValue)

    def wheelEvent(self, event):
        qApp.sendEvent(self.parentWidget(), event)

    def keyPressEvent(self, event):
        qApp.sendEvent(self.parentWidget(), event)

    def setCutMode(self, flag):
        if flag:
            self.sliderGrooveBack1 = '#FFF'
            self.sliderGrooveBack2 = '#FFF'
            self.sliderSubBack1 = '#FFF'
            self.sliderSubBack2 = '#0EB065'
            self.sliderHandleBack1 = '#0EB065'
            self.sliderHandleBack2 = '#0EB065'
            self.sliderHandleHoverBack1 = '#AAA'
            self.sliderHandleHoverBack2 = '#888'
        else:
            self.sliderGrooveBack1 = '#FFF'
            self.sliderGrooveBack2 = '#FFF'
            self.sliderSubBack1 = '#FFF'
            self.sliderSubBack2 = '#6A4572'
            self.sliderHandleBack1 = '#6A4572'
            self.sliderHandleBack2 = '#6A4572'
            self.sliderHandleHoverBack1 = '#AAA'
            self.sliderHandleHoverBack2 = '#888'
        self.setSliderColor()
