#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - a simple yet fast & accurate video cutter & joiner
#
# copyright © 2017 Pete Alexandrou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

import logging
import os
import re
import shlex
import sys
from distutils.spawn import find_executable

from PyQt5.QtCore import QDir, QFileInfo, QObject, QProcess, QProcessEnvironment, QTemporaryFile, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import qApp, QMessageBox


class VideoService(QObject):
    def __init__(self, parent=None):
        super(VideoService, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.consoleOutput = ''
        if sys.platform == 'win32':
            self.backend = os.path.join(self.getAppPath(), 'bin', 'ffmpeg.exe')
            self.mediainfo = os.path.join(self.getAppPath(), 'bin', 'MediaInfo.exe')
            if not os.path.exists(self.backend):
                self.backend = find_executable('ffmpeg.exe')
            if not os.path.exists(self.mediainfo):
                self.mediainfo = find_executable('MediaInfo.exe')
        else:
            self.backend = os.path.join(self.getAppPath(), 'bin', 'ffmpeg')
            self.mediainfo = os.path.join(self.getAppPath(), 'bin', 'mediainfo')
            if not os.path.exists(self.backend):
                for exe in ('ffmpeg', 'avconv'):
                    exe_path = find_executable(exe)
                    if exe_path is not None:
                        self.backend = exe_path
                        break
            if not os.path.exists(self.mediainfo):
                self.mediainfo = find_executable('mediainfo')
        if os.getenv('DEBUG', False):
            try:
                self.logger.info('\nVideoService.backend = %s\nVideoService.mediainfo = %s'
                                 % (self.backend, self.mediainfo))
            except:
                pass
        self.initProc()

    def initProc(self) -> None:
        self.proc = QProcess(self.parent)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        env = QProcessEnvironment.systemEnvironment()
        self.proc.setProcessEnvironment(env)
        self.proc.setWorkingDirectory(self.getAppPath())
        if hasattr(self.proc, 'errorOccurred'):
            self.proc.errorOccurred.connect(self.cmdError)

    def capture(self, source: str, frametime: str) -> QPixmap:
        img, capres = None, QPixmap()
        try:
            img = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX.jpg'))
            if img.open():
                imagecap = img.fileName()
                args = '-ss %s -i "%s" -vframes 1 -s 100x70 -y %s' % (frametime, source, imagecap)
                if self.cmdExec(self.backend, args):
                    capres = QPixmap(imagecap, 'JPG')
        finally:
            del img
        return capres

    def cut(self, source: str, output: str, frametime: str, duration: str) -> bool:
        args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -map 0 -y "%s"' \
               % (source, frametime, duration, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def join(self, filelist: list, output: str) -> bool:
        args = '-f concat -safe 0 -i "%s" -c copy -map 0 -y "%s"' % (filelist, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def streamcount(self, source: str, type: str='audio') -> int:
        m = re.findall('\n^%s' % type.title(), self.metadata(source, type), re.MULTILINE)
        return len(m)

    def metadata(self, source: str, output: str='HTML') -> str:
        args = '--output=%s "%s"' % (output, source)
        result = self.cmdExec(self.mediainfo, args, True)
        return result.strip()

    def cmdExec(self, cmd: str, args: str = None, output: bool = False):
        if os.getenv('DEBUG', False):
            print('VideoService CMD: %s %s' % (cmd, args))
        if self.proc.state() == QProcess.NotRunning:
            self.proc.start(cmd, shlex.split(args))
            self.proc.waitForFinished(-1)
            if output:
                return str(self.proc.readAllStandardOutput(), 'utf-8')
            if self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0:
                return True
        return False

    @pyqtSlot(QProcess.ProcessError)
    def cmdError(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.Crashed:
            QMessageBox.critical(self.parent.parent, '',
                                 '<h4>%s Error:</h4>' % self.backend +
                                 '<p>%s</p>' % self.proc.errorString(), buttons=QMessageBox.Close)
            qApp.quit()

    def getAppPath(self) -> str:
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return QFileInfo(__file__).absolutePath()
