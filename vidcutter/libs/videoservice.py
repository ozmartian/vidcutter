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

from PyQt5.QtCore import pyqtSlot, QDir, QFile, QFileInfo, QObject, QProcess, QProcessEnvironment, QSize, QTemporaryFile
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox


class VideoService(QObject):
    frozen = getattr(sys, 'frozen', False)

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
        TIMELINE = QSize(80, 60)

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
        if VideoService.frozen:
            if sys.platform == 'win32':
                return os.path.join(VideoService.getAppPath(), 'bin', 'ffmpeg.exe'), \
                       os.path.join(VideoService.getAppPath(), 'bin', 'MediaInfo.exe')
            else:
                return os.path.join(VideoService.getAppPath(), 'bin', 'ffmpeg'), \
                       os.path.join(VideoService.getAppPath(), 'bin', 'mediainfo')
        else:
            for exe in VideoService.utils[os.name]['ffmpeg']:
                backend = find_executable(exe)
                if backend is not None:
                    break
            for exe in VideoService.utils[os.name]['mediainfo']:
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
    def capture(source: str, frametime: str, thumbsize: ThumbSize=ThumbSize.INDEX) -> QPixmap:
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

    # def validate(self, source: str) -> bool:
    #     isValid = False
    #     return isValid

    def cut(self, source: str, output: str, frametime: str, duration: str, allstreams: bool=True) -> bool:
        if allstreams:
            args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -scodec copy -map 0 -v 16 -y "%s"' \
                   % (source, frametime, duration, QDir.fromNativeSeparators(output))
        else:
            args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -v 16 -y "%s"' \
                   % (source, frametime, duration, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def join(self, filelist: str, output: str, allstreams: bool=True) -> bool:
        if allstreams:
            args = '-f concat -safe 0 -i "%s" -c copy -map 0 -v 16 -y "%s"' % (filelist,
                                                                               QDir.fromNativeSeparators(output))
        else:
            args = '-f concat -safe 0 -i "%s" -c copy -v 16 -y "%s"' % (filelist,
                                                                        QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def getBSF(self, mediatype: str) -> str:
        media_format = self.parent.mpvWidget.format(mediatype)
        if mediatype == 'video':
            prefix = '-bsf:v'
            if media_format == 'hevc':
                return '%s hevc_mp4toannexb' % prefix
            elif media_format == 'h264':
                return '%s h264_mp4toannexb' % prefix
            elif media_format == 'mpeg4':
                return '%s mpeg4_unpack_bframes' % prefix
            elif media_format in {'webm', 'ivf', 'vp9'}:
                return '%s vp9_superframe' % prefix
        elif mediatype == 'audio':
            prefix = '-bsf:a'
            if media_format == 'aac':
                return '%s aac_adtstoasc' % prefix
            elif media_format == 'mp3':
                return '%s mp3decomp' % prefix
        return ''

    def mpegtsJoin(self, inputs: list, output: str) -> bool:
        result = False
        outfiles = list()
        # 1. transcode to mpeg transport streams
        for file in inputs:
            name, ext = os.path.splitext(file)
            outfile = '%s.ts' % name
            outfiles.append(outfile)
            args = '-i "%s" -c copy -map 0 %s -f mpegts "%s"' % (file, self.getBSF('video'), outfile)
            if not self.cmdExec(self.backend, args):
                return result
        # 2. losslessly concatenate at the file level
        if len(outfiles):
            args = '-i "concat:%s" -c copy %s "%s"' % ('|'.join(map(str, outfiles)),
                                                       self.getBSF('audio'), QDir.fromNativeSeparators(output))
            result = self.cmdExec(self.backend, args)
            # 3. cleanup mpegts files
            [QFile.remove(file) for file in outfiles]
        return result

    def streamcount(self, source: str, stream_type: str='audio') -> int:
        m = re.findall('\n^%s' % stream_type.title(), self.metadata(source, stream_type), re.MULTILINE)
        return len(m)

    def metadata(self, source: str, output: str='HTML') -> str:
        args = '--output=%s "%s"' % (output, source)
        result = self.cmdExec(self.mediainfo, args, True)
        return result.strip()

    def cmdExec(self, cmd: str, args: str=None, output: bool=False):
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

    # noinspection PyUnresolvedReferences, PyProtectedMember
    @staticmethod
    def getAppPath() -> str:
        if VideoService.frozen:
            return sys._MEIPASS
        return QFileInfo(__file__).absolutePath()
