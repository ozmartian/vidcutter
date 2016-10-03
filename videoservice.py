#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import shlex
import sys

from PyQt5.QtCore import QDir, QFileInfo, QObject, QProcess, QTemporaryFile
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox


class VideoService(QObject):
    def __init__(self, parent):
        super(VideoService, self).__init__(parent)
        self.parent = parent
        self.consoleOutput = ''
        self.backend = 'ffmpeg'
        arch = 'x64' if platform.architecture() == '64bit' else 'x86'
        if sys.platform == 'win32':
            self.backend = os.path.join(self.getAppPath(), 'bin', arch, 'ffmpeg.exe')
        self.initProc()

    def initProc(self) -> None:
        self.proc = QProcess(self.parent)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.setWorkingDirectory(self.getAppPath())
        if hasattr(self.proc, 'errorOccurred'):
            self.proc.errorOccurred.connect(self.cmdError)

    def capture(self, source: str, frametime: str) -> QPixmap:
        img, capres = None, None
        try:
            img = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX.jpg'))
            if img.open():
                imagecap = img.fileName()
                args = '-ss %s -i "%s" -vframes 1 -s 100x70 -y %s' % (frametime, source, imagecap)
                self.proc.start(self.backend, shlex.split(args))
                self.proc.waitForFinished(-1)
                if self.proc.exitCode() == 0 and self.proc.exitStatus() == QProcess.NormalExit:
                    capres = QPixmap(imagecap, 'JPG')
        finally:
            del img
        return capres

    def cut(self, source: str, output: str, frametime: str, duration: str) -> bool:
        args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -y "%s"'\
               % (source, frametime, duration, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def join(self, filelist: list, output: str) -> bool:
        args = '-f concat -safe 0 -i "%s" -c copy -y "%s"' % (filelist, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def cmdExec(self, cmd: str, args: list = None) -> bool:
        if self.proc.state() == QProcess.NotRunning:
            self.proc.start(cmd, shlex.split(args))
            self.proc.waitForFinished(-1)
            if self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0:
                return True
        return False

    def cmdError(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.Crashed:
            QMessageBox.critical(self.parent.parent, "Error calling an external process",
                                 self.proc.errorString(), buttons=QMessageBox.Cancel)

    def getAppPath(self) -> str:
        return QFileInfo(__file__).absolutePath()
