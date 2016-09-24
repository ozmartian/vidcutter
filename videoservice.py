#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shlex
import sys
import tempfile

from PyQt5.QtCore import QFileInfo, QObject, QProcess
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
        capres = None
        if sys.platform == 'win32':
            fd, imagecap = tempfile.mkstemp(suffix='.jpg')
            try:
                os.write(fd, b'dummy data')
                os.close(fd)
                args = shlex.split('-ss %s -i "%s" -vframes 1 -s 100x70 -y %s' % (frametime, source, imagecap))
                self.proc.start(self.backend, args)
                self.proc.waitForFinished(-1)
                if self.proc.exitCode() == 0 and self.proc.exitStatus() == QProcess.NormalExit:
                    capres = QPixmap(imagecap, 'JPG')
                # ff = FFmpeg(
                #     executable=self.backend,
                #     inputs={source: '-ss %s' % frametime},
                #     outputs={imagecap: '-vframes 1 -s 100x70 -y'}
                # )
                # ff.run()
            finally:
                os.remove(imagecap)
        else:
            with tempfile.NamedTemporaryFile(suffix='.jpg') as imagecap:
                args = shlex.split('-ss %s -i "%s" -vframes 1 -s 100x70 -y %s' % (frametime, source, imagecap.name))
                self.proc.start(self.backend, args)
                self.proc.waitForFinished(-1)
                if self.proc.exitCode() == 0 and self.proc.exitStatus() == QProcess.NormalExit:
                    capres = QPixmap(imagecap.name, 'JPG')
                # ff = FFmpeg(
                #     executable=self.backend,
                #     inputs={source: '-ss %s' % frametime},
                #     outputs={imagecap.name: '-vframes 1 -s 100x70 -y'}
                # )
                # ff.run()
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

        # if sys.platform == 'win32':
        #     si = subprocess.STARTUPINFO()
        #     si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        #     return subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        #                             stdin=subprocess.PIPE, startupinfo=si, env=os.environ, shell=shell)
        # else:
        #     return subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)

    def cmdError(self, error):
        if error != QProcess.Crashed:
            QMessageBox.critical(None, "Error calling an external process", self.proc.errorString(), buttons=QMessageBox.Cancel)

    def getAppPath(self):
        return QFileInfo(__file__).absolutePath()
