#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSlot
from PyQt5.QtGui import QColor, QKeyEvent, QMouseEvent, QPaintEvent, QWheelEvent
from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider, QStylePainter, QWidget, qApp


class VideoSlider(QSlider):
    def __init__(self, *arg, **kwargs):
        super(VideoSlider, self).__init__(*arg, **kwargs)
        self.setOrientation(Qt.Horizontal)
        self.setObjectName('VideoSlider')
        self.setAttribute(Qt.WA_Hover, True)
        self.setStatusTip('Set clip start and end points')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRange(0, 0)
        self.setSingleStep(1)
        self.setMouseTracking(True)
        self.setTracking(True)
        self.setTickPosition(QSlider.TicksAbove)
        self.setFocus()
        self.initStyle()
        self.restrictValue = 0
        self.valueChanged.connect(self.restrictMove)
        self.installEventFilter(self)

    def initStyle(self, selected: bool = False, margin: str = '0') -> None:
        bground = 'transparent'
        if selected:
            bground = 'rgba(255, 255, 255, 0.75)'
        self.setStyleSheet('''QSlider:horizontal { margin: 25px 0 18px; }
QSlider::groove:horizontal {
    border: 1px inset #999;
    height: 32px;
    background: #444 url(:images/filmstrip.png) repeat-x;
    position: absolute;
    left: 4px;
    right: 4px;
    margin: 0;
}
QSlider::sub-page:horizontal {  
    border: 1px inset #999;
    background: %s;
    height: 20px;
    position: absolute;
    left: 0;
    right: 0;
    margin: 0;
    margin-left: %s;
}
QSlider::add-page:horizontal{
    border: 1px inset #999;
    background: transparent;
}
QSlider::handle:horizontal {
    border: none;
    background: url(:images/handle.png) no-repeat top center;
    width: 20px;
    height: 58px;
    margin: -16px -8px;
}
QSlider::handle:hover {
    background: purple;
}''' % (bground, margin))

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
                    h = 13
                    z = 8
                else:
                    h = 7
                    z = 14
                painter.setPen(QColor('#888'))
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksAbove):
                    y = self.rect().top() + z
                    painter.drawLine(x, y, x, y + h)
                if self.tickPosition() in (QSlider.TicksBothSides, QSlider.TicksBelow):
                    y = self.rect().bottom() - z
                    painter.drawLine(x, y, x, y - h)
                x += 20
        opt.subControls = QStyle.SC_SliderGroove
        painter.drawComplexControl(QStyle.CC_Slider, opt)
        opt.subControls = QStyle.SC_SliderHandle
        painter.drawComplexControl(QStyle.CC_Slider, opt)

    def wheelEvent(self, event: QWheelEvent) -> None:
        qApp.sendEvent(self.parentWidget(), event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        qApp.sendEvent(self.parentWidget(), event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        handle = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        if handle.x() <= event.pos().x() <= (handle.x() + handle.width()):
            self.setCursor(Qt.SplitHCursor)
        else:
            self.unsetCursor()
        super(VideoSlider, self).mouseMoveEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.MouseButtonRelease:
            if self.parentWidget().mediaPlayer.isVideoAvailable() or self.parentWidget().mediaPlayer.isAudioAvailable():
                self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width()))
                self.parentWidget().mediaPlayer.setPosition(self.sliderPosition())
        return QWidget.eventFilter(self, obj, event)
