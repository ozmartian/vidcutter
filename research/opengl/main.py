#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import locale
import signal
import sys

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QMainWindow, QPushButton, QSizePolicy, QSlider,
                             QVBoxLayout, QWidget)

from mpvwidget import MpvWidget

signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.m_mpv = MpvWidget(self)
        self.m_mpv.setMinimumSize(800, 600)
        self.m_slider = QSlider(Qt.Horizontal, self)
        self.m_slider.setDisabled(True)
        m_openBtn = QPushButton('Open')
        self.m_playBtn = QPushButton('Play')
        self.m_playBtn.setDisabled(True)
        hb = QHBoxLayout()
        hb.addStretch(1)
        hb.addWidget(m_openBtn)
        hb.addSpacing(10)
        hb.addWidget(self.m_playBtn)
        hb.addStretch(1)
        vb = QVBoxLayout()
        vb.addWidget(self.m_mpv)
        vb.addWidget(self.m_slider)
        vb.addLayout(hb)
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        widget.setLayout(vb)
        self.setCentralWidget(widget)
        self.m_mpv.mpv.positionChanged.connect(self.m_slider.setValue)
        self.m_mpv.mpv.durationChanged.connect(self.setSliderRange)
        self.m_slider.sliderMoved.connect(self.seek)
        m_openBtn.clicked.connect(self.open)
        self.m_playBtn.clicked.connect(self.pause)

    @pyqtSlot()
    def open(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Open a video')
        if len(file):
            self.m_mpv.mpv.play(file)
            self.m_slider.setEnabled(True)
            self.m_playBtn.setEnabled(True)

    @pyqtSlot()
    def pause(self):
        paused = self.m_mpv.mpv.pause
        self.m_playBtn.setText('Pause' if paused else 'Play')
        self.m_mpv.mpv.pause = not paused

    @pyqtSlot(int)
    def seek(self, pos):
        self.m_mpv.mpv.seek(pos, 'absolute+exact')

    @pyqtSlot(float)
    def setSliderRange(self, duration):
        self.m_slider.setRange(0, int(duration))


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
