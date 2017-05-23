#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
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
#################################################################s######

import logging
import os
import re
import shlex
import sys
from distutils.spawn import find_executable
from enum import Enum

from PyQt5.QtCore import QDir, QFileInfo, QObject, QProcess, QProcessEnvironment, QSize, QTemporaryFile, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox


class VideoService(QObject):

    class ThumbSize(Enum):
        INDEX = QSize(100, 70)
        TIMELINE = QSize(50, 38)

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
                for exe in ('ffmpeg', 'ffmpeg2.8', 'avconv'):
                    exe_path = find_executable(exe)
                    if exe_path is not None:
                        self.backend = exe_path
                        break
            if not os.path.exists(self.mediainfo):
                self.mediainfo = find_executable('mediainfo')
        if os.getenv('DEBUG', False):
            self.logger.info('VideoService: backend = "%s"\tmediainfo = "%s"' % (self.backend, self.mediainfo))
        self.initProc()

    def initProc(self) -> None:
        self.proc = QProcess(self.parent)
        env = QProcessEnvironment.systemEnvironment()
        self.proc.setProcessEnvironment(env)
        self.proc.setWorkingDirectory(self.getAppPath())
        if hasattr(self.proc, 'errorOccurred'):
            self.proc.errorOccurred.connect(self.cmdError)

    def capture(self, source: str, frametime: str, thumbsize: ThumbSize = ThumbSize.INDEX) -> QPixmap:
        img, capres = None, QPixmap()
        try:
            img = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX.jpg'))
            if img.open():
                imagecap = img.fileName()
                size = thumbsize.value
                args = '-ss %s -i "%s" -vframes 1 -s %ix%i -y %s' % (frametime, source, size.width(), size.height(),
                                                                     imagecap)
                if self.cmdExec(self.backend, args):
                    capres = QPixmap(imagecap, 'JPG')
        finally:
            del img
        return capres

    def cut(self, source: str, output: str, frametime: str, duration: str, allstreams: bool = True) -> bool:
        if allstreams:
            args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -scodec copy -map 0 -y "%s"' \
                   % (source, frametime, duration, QDir.fromNativeSeparators(output))
        else:
            args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -y "%s"' \
                   % (source, frametime, duration, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def join(self, filelist: list, output: str, allstreams: bool = True) -> bool:
        if allstreams:
            args = '-f concat -safe 0 -i "%s" -c copy -map 0 -y "%s"' % (filelist, QDir.fromNativeSeparators(output))
        else:
            args = '-f concat -safe 0 -i "%s" -c copy -y "%s"' % (filelist, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def streamcount(self, source: str, stream_type: str = 'audio') -> int:
        m = re.findall('\n^%s' % stream_type.title(), self.metadata(source, stream_type), re.MULTILINE)
        return len(m)

    def metadata(self, source: str, output: str = 'HTML') -> str:
        args = '--output=%s "%s"' % (output, source)
        result = self.cmdExec(self.mediainfo, args, True)
        return result.strip()

    # @staticmethod
    # def streams(source: str) -> dict:
    #     mediainfo = MediaInfo.parse(source).to_data().get('tracks')
    #     return {
    #         'general': [general for general in mediainfo if general['track_type'] == 'General'],
    #         'video': [video for video in mediainfo if video['track_type'] == 'Video'],
    #         'audio': [audio for audio in mediainfo if audio['track_type'] == 'Audio'],
    #         'text': [text for text in mediainfo if text['track_type'] == 'Text'],
    #         'other': [other for other in mediainfo if other['track_type'] == 'Other'],
    #     }

    def cmdExec(self, cmd: str, args: str = None, output: bool = False):
        if os.getenv('DEBUG', False):
            self.logger.info('\nVideoService cmdExec: "%s %s"' % (cmd, args if args is not None else ''))
        if self.proc.state() == QProcess.NotRunning:
            self.proc.setProcessChannelMode(QProcess.SeparateChannels if cmd == self.mediainfo
                                            else QProcess.MergedChannels)
            self.proc.start(cmd, shlex.split(args))
            self.proc.waitForFinished(-1)
            if output:
                return str(self.proc.readAllStandardOutput().data(), 'utf-8')
            if self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0:
                return True
        return False

    @pyqtSlot(QProcess.ProcessError)
    def cmdError(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.Crashed:
            QMessageBox.critical(self.parent.parent, '',
                                 '<h4>%s Error:</h4>' % self.backend +
                                 '<p>%s</p>' % self.proc.errorString(), buttons=QMessageBox.Close)
            # qApp.quit()

    @staticmethod
    def getAppPath() -> str:
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return QFileInfo(__file__).absolutePath()
