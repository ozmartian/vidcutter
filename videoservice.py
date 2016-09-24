#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shlex
import sys

from PyQt5.QtCore import QDir, QFileInfo, QObject, QProcess, QTemporaryFile
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox, QTextEdit


class VideoService(QObject):
    def __init__(self, parent):
        super(VideoService, self).__init__(parent)
        self.parent = parent
        self.consoleOutput = ''
        self.backend = 'ffmpeg'
        if sys.platform == 'win32':
            self.backend = os.path.join(self.getAppPath(), 'bin', 'ffmpeg.exe')
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.setWorkingDirectory(self.getAppPath())
        # self.proc.readyReadStandardOutput.connect(self.readyReadStandardOutput)
        # self.proc.finished.connect(self.finished)
        self.proc.errorOccurred.connect(self.cmdError)
        self.console = QTextEdit(self.parent, readOnly=True, enabled=False, visible=False)

    def imageCapture(self, source, frametime):
        img, capres = None, None
        try:
            img = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX.jpg'))
            if img.open():
                imagecap = img.fileName()
                args = shlex.split('-ss %s -i "%s" -vframes 1 -s 100x70 -y %s' % (frametime, source, imagecap))
                self.proc.start(self.backend, args)
                self.proc.waitForFinished(-1)
                if self.proc.exitCode() == 0 and self.proc.exitStatus() == QProcess.NormalExit:
                    capres = QPixmap(imagecap, 'JPG')
        finally:
            del img
        return capres

    def readyReadStandardOutput(self):
        self.consoleOutput += self.proc.readAllStandardOutput()

    def cmdExec(self, cmd):
        if self.proc.state() == QProcess.NotRunning:
            self.proc.start(cmd)
            self.proc.waitForFinished(-1)
            if self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0:
                return True
        return False

    def cmdError(self, error):
        if error != QProcess.Crashed:
            QMessageBox.critical(None, "Error calling an external process", self.proc.errorString(), buttons=QMessageBox.Cancel)

    def getAppPath(self):
        return QFileInfo(__file__).absolutePath()
