#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import QFileInfo, QObject, QProcess, QProcessEnvironment
from PyQt5.QtWidgets import QMessageBox


class VideoService(QObject):
    def __init__(self, parent):
        super(VideoService, self).__init__(parent)
        self.consoleOutput = ''
        self.backend = 'ffmpeg' if not sys.platform == 'win32' else self.backend =  os.path.join(self.getAppPath(), 'bin', 'ffmpeg.exe')

        self.proc = QProcess(self)

    def cmdExec(self, cmd):
        if self.proc.state() == QProcess.NotRunning:
            self.proc.start(cmd)
            self.proc.waitForFinished(-1)
            if self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0:
                return True
        return False

        # if sys.platform == 'win32':
        #     si = subprocess.STARTUPINFO()
        #     si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        #     return subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        #                             stdin=subprocess.PIPE, startupinfo=si, env=os.environ, shell=shell)
        # else:
        #     return subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)

    def readyReadStandardOutput(self):
        self.consoleOutput += self.proc.readAllStandardOutput()

    def cmdFinished(self, code, status):
        return code == 0 and status == QProcess.NormalExit

    def cmdError(self, error):
        if error != QProcess.Crashed:
            QMessageBox.critical(None, "Error calling an external process", self.proc.errorString(), buttons=QMessageBox.Cancel)

    def getAppPath(self):
        return QFileInfo(__file__).absolutePath()
