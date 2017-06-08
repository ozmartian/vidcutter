#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import locale
# import signal
import shlex
import sys

from PyQt5.QtCore import pyqtSlot, Qt, QProcess, QTemporaryFile
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QMainWindow, QMessageBox, QPushButton, QSizePolicy,
                             QSlider, QVBoxLayout, QWidget)

# signal.signal(signal.SIGINT, signal.SIG_DFL)
# signal.signal(signal.SIGTERM, signal.SIG_DFL)

from mpvwidget import mpvWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.m_mpv = self.initMPV()
        self.m_mpv.setMinimumSize(800, 600)
        self.m_slider = QSlider(Qt.Horizontal, self)
        self.m_slider.setDisabled(True)
        m_openBtn = QPushButton('Open')
        self.m_playBtn = QPushButton('Play')
        self.m_playBtn.setDisabled(True)
        self.m_testBtn = QPushButton('Test')
        self.m_testBtn.setDisabled(True)
        hb = QHBoxLayout()
        hb.addStretch(1)
        hb.addWidget(m_openBtn)
        hb.addSpacing(10)
        hb.addWidget(self.m_playBtn)
        hb.addStretch(1)
        hb.addWidget(self.m_testBtn)
        vb = QVBoxLayout()
        vb.addWidget(self.m_mpv)
        vb.addWidget(self.m_slider)
        vb.addLayout(hb)
        self.widget = QWidget(self)
        self.widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget.setLayout(vb)
        self.setCentralWidget(self.widget)
        # self.m_mpv.mpv.positionChanged.connect(self.m_slider.setValue)
        # self.m_mpv.mpv.durationChanged.connect(self.setSliderRange)
        self.m_slider.sliderMoved.connect(self.seek)
        m_openBtn.clicked.connect(self.open)
        self.m_playBtn.clicked.connect(self.pause)
        self.m_testBtn.clicked.connect(self.test)

    @staticmethod
    def initMPV():
        return mpvWidget(
            pause=True,
            terminal=True,
            msg_level='all=v',
            vo='opengl-cb',
            hwdec='auto',
            hr_seek=False,
            hr_seek_framedrop=True,
            video_sync='display-vdrop',
            audio_file_auto=False,
            quiet=True,
            keep_open=True,
            idle=True,
            observe=['time-pos', 'duration'])

    @pyqtSlot()
    def test(self):
        success = False
        tempfile = QTemporaryFile('/tmp/XXXXXX.jpg')
        proc = QProcess(self)
        if tempfile.open() and proc.state() == QProcess.NotRunning:
            args = '-ss %s -i "%s" -vframes 1 -s %ix%i -y %s' % ('00:00:30', self.file, 50, 38, tempfile.fileName())
            proc.start('ffmpeg', shlex.split(args))
            proc.waitForFinished(-1)
            if proc.exitStatus() == QProcess.NormalExit and proc.exitCode() == 0:
                success = True
        msg = 'Process was successful' if success else 'Process was a failure'
        QMessageBox.information(self, 'Test result', '%s\n\n%s' % (msg, tempfile.fileName()))

    @pyqtSlot()
    def open(self):
        self.file, _ = QFileDialog.getOpenFileName(self.widget, 'Open a video')
        if len(self.file):
            self.m_mpv.mpv.command('loadfile', self.file)
            self.m_slider.setEnabled(True)
            self.m_playBtn.setEnabled(True)
            self.m_testBtn.setEnabled(True)

    @pyqtSlot()
    def pause(self):
        paused = self.m_mpv.mpv.get_property('pause')
        self.m_playBtn.setText('Pause' if paused else 'Play')
        self.m_mpv.mpv.set_property('pause', not paused)

    @pyqtSlot(int)
    def seek(self, pos):
        self.m_mpv.mpv.seek(pos, 'absolute+exact', async=True)

    @pyqtSlot(int)
    def setSliderRange(self, duration):
        self.m_slider.setRange(0, duration)

    def mouseDoubleClickEvent(self, event):
        if self.m_mpv.window().isFullScreen():
            self.m_mpv.window().showNormal()
        else:
            self.m_mpv.window().showFullScreen()
        self.m_mpv.mpv.fullscreen = not self.m_mpv.mpv.fullscreen
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            fs = not self.m_mpv.mpv.fullscreen
            self.m_mpv.showFullScreen() if fs else self.m_mpv.showNormal()
            self.m_mpv.mpv.fullscreen = fs
        super(MainWindow, self).keyPressEvent(event)


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
