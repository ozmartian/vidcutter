#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import locale
import logging
import signal
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import mpv as libmpv


class MPVWidget(QOpenGLWidget):
    def __init__(self, parent=None, **kwargs):
        super(MPVWidget, self).__init__(parent, **kwargs)

        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.mpv = handle



if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    app = QApplication(sys.argv)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    glwidget = MPVWidget()
    glwidget.show()
    sys.exit(app.exec_())
