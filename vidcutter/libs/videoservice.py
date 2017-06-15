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
#######################################################################

import logging
import os
import re
import shlex
import sys
from distutils.spawn import find_executable
from enum import Enum

from PyQt5.QtCore import pyqtSlot, QDir, QFileInfo, QObject, QProcess, QProcessEnvironment, QSize, QTemporaryFile
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox


class VideoService(QObject):
    utils = {
        'nt': {
            'ffmpeg': ['ffmpeg.exe'],
            'mediainfo': ['MediaInfo.exe']
        },
        'posix': {
            'ffmpeg': ['ffmpeg', 'ffmpeg2.8', 'avconv'],
            'mediainfo': ['mediainfo']
        }
    }

    class ThumbSize(Enum):
        INDEX = QSize(100, 70)
        TIMELINE = QSize(50, 38)

    def __init__(self, parent=None):
        super(VideoService, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.backend, self.mediainfo = VideoService.initBackends()
        if self.backend is not None:
            self.proc = VideoService.initProc()
            self.proc.errorOccurred.connect(self.cmdError)

    @staticmethod
    def initBackends() -> tuple:
        backend, mediainfo = None, None
        for exe in VideoService.utils.get(os.name).get('ffmpeg'):
            backend = find_executable(exe)
            if backend is not None:
                break
        for exe in VideoService.utils.get(os.name).get('mediainfo'):
            mediainfo = find_executable(exe)
            if mediainfo is not None:
                break
        return backend, mediainfo

    @staticmethod
    def initProc() -> QProcess:
        p = QProcess()
        p.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        p.setWorkingDirectory(VideoService.getAppPath())
        return p

    @staticmethod
    def capture(source: str, frametime: str, thumbsize: ThumbSize = ThumbSize.INDEX) -> QPixmap:
        capres = QPixmap()
        img = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX.jpg'))
        if img.open():
            imagecap = img.fileName()
            size = thumbsize.value
            backend, _ = VideoService.initBackends()
            args = '-ss %s -i "%s" -vframes 1 -s %ix%i -v 16 -y "%s"' % (frametime, source, size.width(),
                                                                         size.height(), imagecap)
            proc = VideoService.initProc()
            proc.setProcessChannelMode(QProcess.MergedChannels)
            if proc.state() == QProcess.NotRunning:
                if os.getenv('DEBUG', False):
                    logging.getLogger(__name__).info('"%s %s"' % (backend, args))
                proc.start(backend, shlex.split(args))
                proc.waitForFinished(-1)
                if proc.exitStatus() == QProcess.NormalExit and proc.exitCode() == 0:
                    capres = QPixmap(imagecap, 'JPG')
        return capres

    def cut(self, source: str, output: str, frametime: str, duration: str, allstreams: bool = True) -> bool:
        if allstreams:
            args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -scodec copy -map 0 -v 16 -y "%s"' \
                   % (source, frametime, duration, QDir.fromNativeSeparators(output))
        else:
            args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -v 16 -y "%s"' \
                   % (source, frametime, duration, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def join(self, filelist: str, output: str, allstreams: bool = True) -> bool:
        if allstreams:
            args = '-f concat -safe 0 -i "%s" -c copy -map 0 -v 16 -y "%s"' % (filelist,
                                                                               QDir.fromNativeSeparators(output))
        else:
            args = '-f concat -safe 0 -i "%s" -c copy -v 16 -y "%s"' % (filelist,
                                                                        QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def streamcount(self, source: str, stream_type: str = 'audio') -> int:
        m = re.findall('\n^%s' % stream_type.title(), self.metadata(source, stream_type), re.MULTILINE)
        return len(m)

    def metadata(self, source: str, output: str = 'HTML') -> str:
        args = '--output=%s "%s"' % (output, source)
        result = self.cmdExec(self.mediainfo, args, True)
        return result.strip()

    def cmdExec(self, cmd: str, args: str = None, output: bool = False):
        if os.getenv('DEBUG', False):
            self.logger.info('"%s %s"' % (cmd, args if args is not None else ''))
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
            QMessageBox.critical(self.parent, '',
                                 '<h4>%s Error:</h4>' % self.backend +
                                 '<p>%s</p>' % self.proc.errorString(), buttons=QMessageBox.Close)

    @staticmethod
    def getAppPath() -> str:
        if getattr(sys, 'frozen', False):
            # noinspection PyProtectedMember
            return sys._MEIPASS
        return QFileInfo(__file__).absolutePath()

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
