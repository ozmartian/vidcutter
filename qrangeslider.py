#!/usr/bin/env python3

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class RangeSlider(QSlider):
    """ A slider for ranges.

        This class provides a dual-slider for ranges, where there is a defined
        maximum and minimum, as is a normal slider, but instead of having a
        single slider value, there are 2 slider values.

        This class emits the same signals as the QSlider base class, with the
        exception of valueChanged
    """

    def __init__(self, *args):
        super(RangeSlider, self).__init__(*args)
        # self.init_style()
        self._low = self.minimum()
        self._high = self.maximum()
        self.pressed_control = QStyle.SC_None
        self.hover_control = QStyle.SC_None
        self.click_offset = 0
        # 0 for the low, 1 for the high, -1 for both
        self.active_slider = 0

    def low(self):
        return self._low

    def setLow(self, low):
        self._low = low
        self.update()

    def high(self):
        return self._high

    def setHigh(self, high):
        self._high = high
        self.update()

    def init_style(self) -> None:
        self.setStyleSheet('''
  QSlider::groove:horizontal {
      border: 1px solid #999999;
      height: 8px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */
      background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
      margin: 2px 0;
  }

  QSlider::handle:horizontal {
      background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
      border: 1px solid #5c5c5c;
      width: 18px;
      margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
      border-radius: 3px;
  }
            ''')
#         self.setStyleSheet('''QSlider:horizontal { margin: 25px 0 15px; }
# QSlider::groove:horizontal {
#     border: 1px inset #999;
#     height: 32px;
#     background: #444 url(images/filmstrip.png) repeat-x;
#     position: absolute;
#     left: 0;
#     right: 0;
#     margin: 0;
# }
# QSlider::sub-page:horizontal {
#     border: 1px inset #999;
#     background: rgba(255, 255, 255, 0.6);
#     height: 20px;
#     position: absolute;
#     left: 0;
#     right: 0;
#     margin: 0;
# }
# QSlider::handle:horizontal {
#     border: none;
#     background: url(images/handle.png) no-repeat top center;
#     width: 20px;
#     height: 58px;
#     margin: -18px 0;
# }''')

    def paintEvent(self, event):
        painter = QStylePainter(self)
        # bpainter = QPainter(self)
        style = qApp.style()
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        for i, value in enumerate([self._low, self._high]):
            # Only draw the groove for the first slider so it doesn't get drawn
            # on top of the existing ones every time
            if i == 0:
                opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderHandle
            else:
                opt.subControls = QStyle.SC_SliderHandle
            if self.tickPosition() != self.NoTicks:
                opt.subControls |= QStyle.SC_SliderTickmarks
            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
                opt.state |= QStyle.State_Sunken
            else:
                opt.activeSubControls = self.hover_control
            opt.sliderPosition = value
            opt.sliderValue = value
            # style.drawComplexControl(QStyle.CC_Slider, opt, painter, self)
            painter.drawComplexControl(QStyle.CC_Slider, opt)

    def mousePressEvent(self, event):
        event.accept()
        style = qApp.style()
        button = event.button()
        # In a normal slider control, when the user clicks on a point in the
        # slider's total range, but not on the slider part of the control the
        # control would jump the slider value to where the user clicked.port
        # For this control, clicks which are not direct hits will slide both
        # slider parts
        if button:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            self.active_slider = -1
            for i, value in enumerate([self._low, self._high]):
                opt.sliderPosition = value
                hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
                if hit == style.SC_SliderHandle:
                    self.active_slider = i
                    self.pressed_control = hit
                    self.triggerAction(self.SliderMove)
                    self.setRepeatAction(self.SliderNoAction)
                    self.setSliderDown(True)
                    break
            if self.active_slider < 0:
                self.pressed_control = QStyle.SC_SliderHandle
                self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.pressed_control != QStyle.SC_SliderHandle:
            event.ignore()
            return
        event.accept()
        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self._high += offset
            self._low += offset
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff
        elif self.active_slider == 0:
            if new_pos >= self._high:
                new_pos = self._high - 1
            self._low = new_pos
        else:
            if new_pos <= self._low:
                new_pos = self._low + 1
            self._high = new_pos
        self.click_offset = new_pos
        self.update()
        self.sliderMoved.emit(new_pos)

    def __pick(self, pt):
        if self.orientation() == Qt.Horizontal:
            return pt.x()
        else:
            return pt.y()

    def __pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        style = qApp.style()
        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)
        if self.orientation() == Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1
        return style.sliderValueFromPosition(self.minimum(), self.maximum(), pos - slider_min, slider_max - slider_min, opt.upsideDown)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    slider = RangeSlider(Qt.Horizontal, None)
    slider.setTickInterval(1000)
    slider.setTickPosition(QSlider.TicksBothSides)
    slider.setMinimum(0)
    slider.setMaximum(10000)
    slider.setLow(2000)
    slider.setHigh(8000)
    slider.setMinimumWidth(500)
    slider.setStyleSheet('''
  QSlider::groove:horizontal {
      border: 1px solid #999999;
      height: 8px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */
      background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
      margin: 2px 0;
  }

  QSlider::handle:horizontal {
      background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
      border: 1px solid #5c5c5c;
      width: 18px;
      margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
      border-radius: 3px;
  }
        ''')
    slider.sliderMoved.connect(print)
    slider.show()
    sys.exit(app.exec_())
