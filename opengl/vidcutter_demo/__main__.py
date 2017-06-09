#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import locale
# import signal
import shlex
import sys
from distutils.spawn import find_executable

from PyQt5.QtCore import pyqtSlot, Qt, QProcess, QTemporaryFile
from PyQt5.QtWidgets import (QApplication, QDialogButtonBox, QFileDialog, QMainWindow, QMessageBox, QPushButton,
                             QSizePolicy, QSlider, QVBoxLayout, QWidget)

# signal.signal(signal.SIGINT, signal.SIG_DFL)
# signal.signal(signal.SIGTERM, signal.SIG_DFL)

# noinspection PyUnresolvedReferences
from .mpvwidget import mpvWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.currentMedia = None

        self.m_mpv = mpvWidget(
            # pause=True,
            parent=self,
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
            idle=True)

        self.m_slider = QSlider(Qt.Horizontal, self)
        self.m_slider.setDisabled(True)

        self.m_openBtn = QPushButton('Open')
        self.m_openBtn.setDefault(True)
        self.m_playBtn = QPushButton('Play')
        self.m_playBtn.setDisabled(True)
        self.m_testBtn = QPushButton('Test')
        self.m_testBtn.setDisabled(True)

        self.buttons = QDialogButtonBox(Qt.Horizontal, self)
        self.buttons.setCenterButtons(True)
        self.buttons.addButton(self.m_openBtn, QDialogButtonBox.ActionRole)
        self.buttons.addButton(self.m_playBtn, QDialogButtonBox.ActionRole)
        self.buttons.addButton(self.m_testBtn, QDialogButtonBox.ActionRole)

        vb = QVBoxLayout()
        vb.addWidget(self.m_mpv)
        vb.addWidget(self.m_slider)
        vb.addWidget(self.buttons)

        self.widget = QWidget(self)
        self.widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget.setLayout(vb)
        self.setCentralWidget(self.widget)

        self.m_mpv.positionChanged.connect(self.m_slider.setValue)
        self.m_mpv.durationChanged.connect(lambda val: self.m_slider.setRange(0, val))
        self.m_slider.sliderMoved.connect(self.m_mpv.seek)
        self.m_openBtn.clicked.connect(self.open)
        self.m_playBtn.clicked.connect(self.pause)
        self.m_testBtn.clicked.connect(self.test)

    @pyqtSlot()
    def test(self):
        success = False
        tempfile = QTemporaryFile('XXXXXX.jpg')
        proc = QProcess(self)
        if tempfile.open() and proc.state() == QProcess.NotRunning:
            args = '-ss %s -i "%s" -vframes 1 -s %ix%i -y %s' % ('00:00:30', self.currentMedia,
                                                                 50, 38, tempfile.fileName())
            proc.start(find_executable('ffmpeg'), shlex.split(args))
            proc.waitForFinished(-1)
            if proc.exitStatus() == QProcess.NormalExit and proc.exitCode() == 0:
                success = True
        msg = 'Process was successful' if success else 'Process was a failure'
        QMessageBox.information(self, 'Test result', '%s\n\n%s' % (msg, tempfile.fileName()))

    @pyqtSlot()
    def open(self):
        file, _ = QFileDialog.getOpenFileName(self.widget, 'Open a video')
        if len(file):
            self.currentMedia = file
            self.m_slider.setEnabled(True)
            self.m_playBtn.setEnabled(True)
            self.m_playBtn.setDefault(True)
            self.m_playBtn.setText('Pause')
            self.m_testBtn.setEnabled(True)
            self.m_mpv.play(self.currentMedia)

    @pyqtSlot()
    def pause(self):
        paused = self.m_mpv.mpv.get_property('pause')
        self.m_playBtn.setText('Pause' if paused else 'Play')
        self.m_mpv.mpv.set_property('pause', not paused)



def main():
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
