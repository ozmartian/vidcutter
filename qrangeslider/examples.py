#!/usr/bin/env python

import os
import sys

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic

from qrangeslider import QRangeSlider

app = QtGui.QApplication(sys.argv)

# Example 1
rs1 = QRangeSlider()
rs1.show()
rs1.setWindowTitle('example 1')
rs1.setRange(15, 35)
rs1.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222, stop:1 #333);')
rs1.setSpanStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #282, stop:1 #393);')

# Example 2
rs2 = QRangeSlider()
rs2.show()
rs2.setWindowTitle('example 2')
rs2.setFixedWidth(400)
rs2.setFixedHeight(36)
rs2.setMin(0)
rs2.setMax(100)
rs2.setRange(30, 80)
rs2.setDrawValues(False)
rs2.setStyleSheet("""
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
""")

# Example 3
rs3 = QRangeSlider()
rs3.show()
rs3.setWindowTitle('example 3')
rs3.setFixedHeight(50)
rs3.setMin(0)
rs3.setMax(2000)
rs3.setRange(500, 1253)
rs3.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #aaa, stop:1 #777);')
rs3.handle.setStyleSheet('background: url(data/sin.png) repeat-x; border: 0px;')
rs3.setStyleSheet("""
QRangeSlider > QSplitter::handle {
    background: #777;
    border: 1px solid #555;
}
QRangeSlider > QSplitter::handle:vertical {
    height: 2px;
}
QRangeSlider > QSplitter::handle:pressed {
    background: #ca5;
}
""")
rs3.handle.setTextColor(150)

app.exec_()
