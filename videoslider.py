#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QPoint, Qt
# from PyQt5.QtGui import QRegion, QPainter, QPen
from PyQt5.QtWidgets import QSlider, QStyleFactory, QStyle, QStyleOptionSlider, QToolTip, qApp

from qrangeslider import QRangeSlider


class VideoRanger(QRangeSlider):
    def __init__(self, parent):
        super(VideoRanger, self).__init__(parent)

        # self.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222, stop:1 #333);')
        # self.setSpanStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #282, stop:1 #393);')

        self.setFixedWidth(400)
        self.setFixedHeight(36)
        self.setMin(0)
        self.setMax(100)
        self.setRange(30, 80)
        self.setDrawValues(False)
        self.handle.setTextColor(Qt.darkMagenta)
        self.setStyleSheet('''
QRangeSlider * {
    border: 0px;
    padding: 0px;
}
QRangeSlider #Head {
    background: url(data/filmstrip.png) repeat-x;
}
QRangeSlider #Span {
    background: url(data/clip.png) repeat-x;
}
QRangeSlider #Tail {
    background: url(data/filmstrip.png) repeat-x;
}
QRangeSlider > QSplitter::handle {
    background: #fff;
}
QRangeSlider > QSplitter::handle:vertical {
    height: 2px;
}
QRangeSlider > QSplitter::handle:pressed {
    background: #ca5;
}
''')
        self.show()


class VideoSlider(QSlider):
    def __init__(self, *arg, **kwargs):
        super(VideoSlider, self).__init__(*arg, **kwargs)
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
        self.posLocal, self.posGlobal = 0, 0
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
    height: 14px;
    margin: -14px -2px;
    border-radius: 2px;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %s, stop:1 %s);
}''' % (self.grooveBack1, self.grooveBack2, self.subBack1, self.subBack2, self.handleBack1, self.handleBack2,
        self.handleHoverBack1, self.handleHoverBack2)
        self.setStyleSheet(self.sliderQSS)

    def setRestrictValue(self, value):
        self.restrictValue = value

    def restrictMove(self, value):
        if value < self.restrictValue:
            self.setSliderPosition(self.restrictValue)
            self.releaseMouse()
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

    # def paintEvent(self, event):
    #     self.initStyleOption(self.opt)
    #     rectHandle = self.style.subControlRect(self.style.CC_Slider, self.opt, self.style.SC_SliderHandle)
    #     painter = QPainter(self)
    #     pen = QPen(Qt.NoPen)
    #     painter.setPen(pen)
    #     painter.fillRect(0, 0, QStyle.sliderPositionFromValue(0, self.maximum(), self.sliderPosition(), self.width()), self.height(), Qt.white)
    #     painter.fillRect(0, 0, 0.3 * self.width(), self.height(), Qt.magenta)

    def wheelEvent(self, event):
        qApp.sendEvent(self.parentWidget(), event)

    def keyPressEvent(self, event):
        qApp.sendEvent(self.parentWidget(), event)
