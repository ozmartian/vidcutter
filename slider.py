#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QPaintEvent
from PyQt5.QtWidgets import QSlider, QStyle, QStyleFactory, QStylePainter, QStyleOptionSlider


class VideoSlider(QSlider):
    def __init__(self, *arg, **kwargs):
        super(VideoSlider, self).__init__(*arg, **kwargs)
        self.sliderQSS = '''QSlider:horizontal { margin: 12px 5px; }
QSlider::groove:horizontal {
    border: 1px inset #999;
    background: #FFF; /* qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF, stop:1 #FFF); */
    height: 8px;
    position: absolute;
    left: 2px;
    right: 2px;
    margin: -2px 0;
}
QSlider::sub-page:horizontal {
    border: 1px solid #999;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #59acff, stop:1 #59acff);
    height: 8px;
    position: absolute;
    left: 2px;
    right: 2px;
    margin: -2px 0;
}
QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #CCC, stop:1 #BBB);
    border: 1px solid #777;
    width: 10px;
    height: 12px;
    margin: -12px -2px;
    border-radius: 2px;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #AAA, stop:1 #888);
}'''
        self.setStyleSheet(self.sliderQSS)
        self.setOrientation(Qt.Horizontal)
        self.setStatusTip('Set video frame position')
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimum(0)
        self.setMaximum(0)
        self.setSingleStep(1)
        self.setStyle(QStyleFactory.create('Windows'))
        self.setTickPosition(QSlider.TicksBothSides)
        self.setTickInterval(1)

    def paintEvent(self, event):
        self.handle = self.style()
