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

from PyQt5.QtCore import (pyqtSlot, QDir, QFile, QFileInfo, QObject, QProcess, QProcessEnvironment, QSize,
                          QTemporaryFile, QTime)
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QMessageBox


class VideoService(QObject):
    frozen = getattr(sys, 'frozen', False)

    mpegCodecs = {'h264', 'hevc', 'mpeg4', 'divx', 'xvid', 'webm', 'ivf', 'vp9', 'mpeg2video', 'mpg2',
                     'mp2', 'mp3', 'aac'}

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

    class Stream(Enum):
        AUDIO = 0
        VIDEO = 1
        SUBTITLE = 2

    def __init__(self, parent=None):
        super(VideoService, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.backend, self.mediainfo = VideoService.initBackends()
        if self.backend is not None:
            self.proc = VideoService.initProc()
            self.proc.errorOccurred.connect(self.cmdError)
            self.lastError = ''

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
    def capture(source: str, frametime: str, thumbsize: ThumbSize=ThumbSize.INDEX, external: bool=False) -> QPixmap:
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
                if external:
                    painter = QPainter(capres)
                    painter.drawPixmap(0, 0, QPixmap(':/images/external.png', 'PNG'))
                    painter.end()
        return capres

    def testJoin(self, file1: str, file2: str) -> bool:
        result = False
        self.logger.info('attempting to test joining of "%s" + "%s"' % (file1, file2))
        try:
            # 1. check frame sizes are equal before attempting any further testing
            size1 = self.framesize(file1)
            size2 = self.framesize(file2)
            if size1 != size2:
                self.lastError = '<p>The frame size of this media file differs to the files in your clip index.</p>' + \
                                 '<ul><li>Current files are <b>%sx%s</b><li><li>New file is <b>%sx%s</b></li></ul>' \
                                 % (size1.width(), size1.height(), size2.width(), size2.height())
                return result
            # 2. generate temporary file handles
            _, ext = os.path.splitext(file1)
            file1_cut = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX%s' % ext))
            file2_cut = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX%s' % ext))
            final_join = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX%s' % ext))
            # 3. produce 2 sec long clips from input files
            if file1_cut.open() and file2_cut.open() and final_join.open():
                result1 = self.cut(file1, file1_cut.fileName(), '00:00:00.000', '00:00:02.00', False)
                result2 = self.cut(file2, file2_cut.fileName(), '00:00:00.000', '00:00:02.00', False)
                if result1 and result2:
                    # 4. attempt join using two supported methods
                    if self.isMPEGcodec(file1_cut.fileName()) and self.isMPEGcodec(file2_cut.fileName()):
                        result = self.mpegtsJoin([file1_cut.fileName(), file2_cut.fileName()], final_join.fileName())
                        if not result:
                            result = self.join([file1_cut.fileName(), file2_cut.fileName()],
                                               final_join.fileName(), False)
            file1_cut.remove()
            file2_cut.remove()
            final_join.remove()
        except:
            self.logger.exception('Exception in VideoService.testJoin()', exc_info=True)
            result = False
        return result

    def framesize(self, source: str) -> QSize:
        args = '-i "%s" -hide_banner' % source
        result = self.cmdExec(self.backend, args, True)
        matches = re.search(r'Stream.*Video:.*[,\s](?P<width>\d+?)x(?P<height>\d+?)[,\s]',
                            result, re.DOTALL).groupdict()
        return QSize(int(matches['width']), int(matches['height']))

    def duration(self, source: str) -> QTime:
        args = '-i "%s" -hide_banner' % source
        result = self.cmdExec(self.backend, args, True)
        matches = re.search(r'Duration:\s{1}(?P<hrs>\d+?):(?P<mins>\d+?):(?P<secs>\d+\.\d+?),',
                            result, re.DOTALL).groupdict()
        secs, msecs = matches['secs'].split('.')
        return QTime(int(matches['hrs']), int(matches['mins']), int(secs), int(msecs))

    def codecs(self, source: str) -> tuple:
        args = '-i "%s" -hide_banner' % source
        result = self.cmdExec(self.backend, args, True)
        vcodec = re.search(r'Stream.*Video: (\w+)', result).group(1)
        acodec = re.search(r'Stream.*Audio: (\w+)', result).group(1)
        return vcodec, acodec

    def cut(self, source: str, output: str, frametime: str, duration: str, allstreams: bool=True) -> bool:
        if allstreams:
            args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -scodec copy -map 0 -v 16 -y "%s"' \
                   % (source, frametime, duration, QDir.fromNativeSeparators(output))
        else:
            args = '-i "%s" -ss %s -t %s -vcodec copy -acodec copy -v 16 -y "%s"' \
                   % (source, frametime, duration, QDir.fromNativeSeparators(output))
        return self.cmdExec(self.backend, args)

    def join(self, inputs: list, output: str, allstreams: bool=True) -> bool:
        filelist = os.path.normpath(os.path.join(os.path.dirname(inputs[0]), '_vidcutter.list'))
        fobj = open(filelist, 'w')
        [fobj.write('file \'%s\'\n' % file.replace("'", "\\'")) for file in inputs]
        fobj.close()
        if allstreams:
            args = '-f concat -safe 0 -i "%s" -c copy -map 0 -v 16 -y "%s"' % (filelist,
                                                                               QDir.fromNativeSeparators(output))
        else:
            args = '-f concat -safe 0 -i "%s" -c copy -v 16 -y "%s"' % (filelist,
                                                                        QDir.fromNativeSeparators(output))
        result = self.cmdExec(self.backend, args)
        os.remove(filelist)
        return result

    def getBSF(self, source: str) -> tuple:
        vbsf, absf = '', ''
        vcodec, acodec = self.codecs(source)
        if vcodec:
            prefix = '-bsf:v'
            if vcodec == 'hevc':
                vbsf = '%s hevc_mp4toannexb' % prefix
            elif vcodec == 'h264':
                vbsf = '%s h264_mp4toannexb' % prefix
            elif vcodec == 'mpeg4':
                vbsf = '%s mpeg4_unpack_bframes' % prefix
            elif vcodec in {'webm', 'ivf', 'vp9'}:
                vbsf = '%s vp9_superframe' % prefix
        if acodec:
            prefix = '-bsf:a'
            if acodec == 'aac':
                absf = '%s aac_adtstoasc' % prefix
            elif acodec == 'mp3':
                absf = '%s mp3decomp' % prefix
        return vbsf, absf

    def isMPEGcodec(self, source: str) -> bool:
        return self.codecs(source)[0].lower() in self.mpegCodecs

    def mpegtsJoin(self, inputs: list, output: str) -> bool:
        result = False
        try:
            outfiles = list()
            video_bsf, audio_bsf = self.getBSF(inputs[0])
            # 1. transcode to mpeg transport streams
            for file in inputs:
                name, _ = os.path.splitext(file)
                outfile = '%s.ts' % name
                outfiles.append(outfile)
                if os.path.isfile(outfile):
                    os.remove(outfile)
                args = '-i "%s" -c copy -map 0 %s -f mpegts -v 16 "%s"' % (file, video_bsf, outfile)
                if not self.cmdExec(self.backend, args):
                    return result
            # 2. losslessly concatenate at the file level
            if len(outfiles):
                if os.path.isfile(output):
                    os.remove(output)
                args = '-i "concat:%s" -c copy %s -v 16 "%s"' % ('|'.join(map(str, outfiles)), audio_bsf,
                                                                 QDir.fromNativeSeparators(output))
                result = self.cmdExec(self.backend, args)
                # 3. cleanup mpegts files
                [QFile.remove(file) for file in outfiles]
        except:
            self.logger.exception('Exception in VideoService.mpegtsJoin()', exc_info=True)
            result = False
        return result

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

    # def streamcount(self, source: str, stream: Stream=Stream.AUDIO) -> int:
    #     m = re.findall('\n^%s' % stream_type.title(), self.metadata(source, stream_type), re.MULTILINE)
    #     return len(m)
