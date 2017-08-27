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
from bisect import bisect_left
from distutils.spawn import find_executable
from enum import Enum

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QDir, QFile, QFileInfo, QObject, QProcess, QProcessEnvironment, QSize,
                          QStorageInfo, QTemporaryFile, QTime)
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QMessageBox


class VideoService(QObject):
    updateProgress = pyqtSignal(int, str)
    setProgressRange = pyqtSignal(int, int)

    frozen = getattr(sys, 'frozen', False)

    spaceWarningThreshold = 200
    spaceWarningDelivered = False

    mpegCodecs = {'h264', 'hevc', 'mpeg4', 'divx', 'xvid', 'webm', 'ivf', 'vp9', 'mpeg2video', 'mpg2',
                  'mp2', 'mp3', 'aac'}

    utils = {
        'nt': {
            'ffmpeg': ['ffmpeg.exe'],
            'ffprobe': ['ffprobe.exe'],
            'mediainfo': ['MediaInfo.exe']
        },
        'posix': {
            'ffmpeg': ['ffmpeg', 'ffmpeg2.8', 'avconv'],
            'ffprobe': ['ffprobe', 'avprobe'],
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
        self.backend, self.probe, self.mediainfo = VideoService.initBackends()
        if self.backend is not None:
            self.proc = VideoService.initProc()
            if hasattr(self.proc, 'errorOccurred'):
                self.proc.errorOccurred.connect(self.cmdError)
            self.lastError = ''

    @staticmethod
    def initBackends() -> tuple:
        if VideoService.frozen:
            if sys.platform == 'win32':
                return os.path.join(VideoService.getAppPath(), 'bin', 'ffmpeg.exe'), \
                       os.path.join(VideoService.getAppPath(), 'bin', 'ffprobe.exe'), \
                       os.path.join(VideoService.getAppPath(), 'bin', 'MediaInfo.exe')
            else:
                return os.path.join(VideoService.getAppPath(), 'bin', 'ffmpeg'), \
                       os.path.join(VideoService.getAppPath(), 'bin', 'ffprobe'), \
                       os.path.join(VideoService.getAppPath(), 'bin', 'mediainfo')
        else:
            backend, probe, mediainfo = None, None, None
            for exe in VideoService.utils[os.name]['ffmpeg']:
                backend = find_executable(exe)
                if backend is not None:
                    break
            for exe in VideoService.utils[os.name]['ffprobe']:
                probe = find_executable(exe)
                if probe is not None:
                    break
            for exe in VideoService.utils[os.name]['mediainfo']:
                mediainfo = find_executable(exe)
                if mediainfo is not None:
                    break
            return backend, probe, mediainfo

    @staticmethod
    def initProc() -> QProcess:
        p = QProcess()
        p.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        p.setWorkingDirectory(VideoService.getAppPath())
        return p

    def checkDiskSpace(self, path: str):
        # noinspection PyCallByClass
        if self.spaceWarningDelivered or not QFileInfo.exists(path):
            return
        info = QStorageInfo(path)
        available = info.bytesAvailable() / 1000 / 1000
        if available < VideoService.spaceWarningThreshold:
            warnmsg = "There is less than {0}MB of disk space available at the target folder selected to save " \
                      "your media. VidCutter WILL FAIL to produce your media if you run out of space during " \
                      "operations."
            QMessageBox.warning(self.parent, 'Disk space is low!', warnmsg.format(VideoService.spaceWarningThreshold))
            self.spaceWarningDelivered = True

    @staticmethod
    def capture(source: str, frametime: str, thumbsize: ThumbSize=ThumbSize.INDEX, external: bool=False) -> QPixmap:
        capres = QPixmap()
        img = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX.jpg'))
        if img.open():
            imagecap = img.fileName()
            size = thumbsize.value
            backend, _, _ = VideoService.initBackends()
            args = '-hide_banner -ss %s -i "%s" -vframes 1 -s %ix%i -y "%s"' % (frametime, source, size.width(),
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
        img.remove()
        return capres

    # noinspection PyBroadException
    def testJoin(self, file1: str, file2: str) -> bool:
        result = False
        self.logger.info('attempting to test joining of "%s" + "%s"' % (file1, file2))
        try:
            # 1. check audio + video codecs
            file1_codecs = self.codecs(file1)
            file2_codecs = self.codecs(file2)
            if file1_codecs != file2_codecs:
                self.logger.info('join test failed for %s and %s: codecs mismatched' % (file1, file2))
                self.lastError = '<p>The audio + video format of this media file is not the same as the files ' \
                                 'already in your clip index.</p>' \
                                 '<div align="center">Current files are <b>{0}</b> (video) and ' \
                                 '<b>{1}</b> (audio)<br/>' \
                                 'Failed media is <b>{2}</b> (video) and <b>{3}</b> (audio)</div>'
                self.lastError = self.lastError.format(file1_codecs[0], file1_codecs[1],
                                                       file2_codecs[0], file2_codecs[1])
                return result
            # 2. check frame sizes
            size1 = self.framesize(file1)
            size2 = self.framesize(file2)
            if size1 != size2:
                self.logger.info('join test failed for %s and %s: frame size mismatched' % (file1, file2))
                self.lastError = '<p>The frame size of this media file is not the same as the files already in ' \
                                 'your clip index.</p>' \
                                 '<div align="center">Current media clips are <b>{0}x{1}</b>' \
                                 '<br/>Failed media file is <b>{2}x{3}</b></div>'
                self.lastError = self.lastError.format(size1.width(), size1.height(), size2.width(), size2.height())
                return result
            # 2. generate temporary file handles
            _, ext = os.path.splitext(file1)
            file1_cut = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX%s' % ext))
            file2_cut = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX%s' % ext))
            final_join = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX%s' % ext))
            # 3. produce 4 secs clips from input files for join test
            if file1_cut.open() and file2_cut.open() and final_join.open():
                result1 = self.cut(file1, file1_cut.fileName(), '00:00:00.000', '00:00:04.00', False)
                result2 = self.cut(file2, file2_cut.fileName(), '00:00:00.000', '00:00:04.00', False)
                if result1 and result2:
                    # 4. attempt join of temp 2 second clips
                    result = self.join([file1_cut.fileName(), file2_cut.fileName()], final_join.fileName(), False)
            file1_cut.remove()
            file2_cut.remove()
            final_join.remove()
        except:
            self.logger.exception('Exception in VideoService.testJoin', exc_info=True)
            result = False
        return result

    def framesize(self, source: str) -> QSize:
        args = '-i "%s"' % source
        result = self.cmdExec(self.backend, args, True)
        matches = re.search(r'Stream.*Video:.*[,\s](?P<width>\d+?)x(?P<height>\d+?)[,\s]',
                            result, re.DOTALL).groupdict()
        return QSize(int(matches['width']), int(matches['height']))

    def duration(self, source: str) -> QTime:
        args = '-i "%s"' % source
        result = self.cmdExec(self.backend, args, True)
        matches = re.search(r'Duration:\s(?P<hrs>\d+?):(?P<mins>\d+?):(?P<secs>\d+\.\d+?),',
                            result, re.DOTALL).groupdict()
        secs, msecs = matches['secs'].split('.')
        return QTime(int(matches['hrs']), int(matches['mins']), int(secs), int(msecs))

    def codecs(self, source: str) -> tuple:
        args = '-i "%s"' % source
        result = self.cmdExec(self.backend, args, True)
        vcodec = re.search(r'Stream.*Video:\s(\w+)', result).group(1)
        acodec = re.search(r'Stream.*Audio:\s(\w+)', result).group(1)
        return vcodec, acodec

    def cut(self, source: str, output: str, frametime: str, duration: str, allstreams: bool=True,
            codecs: str=None, loglevel: str='error') -> bool:
        self.checkDiskSpace(output)
        if allstreams:
            if codecs is not None:
                args = '-v {5} -i "{0}" -ss {1} -t {2} -c:v {3} -c:a copy -c:s copy -map 0 -y "{4}"'
                return self.cmdExec(self.backend, args.format(source, frametime, duration, codecs, output, loglevel))
            else:
                args = '-v {4} -ss {1} -i "{0}" -t {2} -c copy -map 0 -avoid_negative_ts 1 -copyinkf -y "{3}"'
                return self.cmdExec(self.backend, args.format(source, frametime, duration, output, loglevel))
        else:
            if codecs is not None:
                args = '-v {5} -i "{0}" -ss {1} -t {2} -c:v {3} -c:a copy -c:s copy -y "{4}"'
                return self.cmdExec(self.backend, args.format(source, frametime, duration, codecs, output, loglevel))
            else:
                args = '-v {4} -ss {1} -i "{0}" -t {2} -c copy -avoid_negative_ts 1 -copyinkf -y "{3}"'
                return self.cmdExec(self.backend, args.format(source, frametime, duration, output, loglevel))

    def smartcut(self, source: str, output: str, start: float, end: float, allstreams: bool=True) -> bool:
        # 1. split output filename
        output_file, output_ext = os.path.splitext(source)
        # 2. get GOP bisections for start and end of clip times to be reencoded for frame accurate cuts
        #    smartcut -> list: start, end, duration, filename
        bisections = self.getGOPbisections(source, start, end)
        smartcut = {
            'start': [start, bisections['start'][1], (bisections['start'][1] - start),
                      '{0}_start{1}'.format(output_file, output_ext)],
            'middle': [bisections['start'][2], bisections['end'][0], (bisections['end'][0] - bisections['start'][2]),
                       '{0}_middle{1}'.format(output_file, output_ext)],
            'end': [bisections['end'][1], end, (end - bisections['end'][1]),
                    '{0}_end{1}'.format(output_file, output_ext)]
        }
        self.logger.info(smartcut)
        # 3. cut middle portion first
        self.setProgressRange.emit(0, 5)
        self.updateProgress.emit(1, '<b>SmartCut</b> : cutting main video chunk [1/5]...')
        middle_result = self.cut(source=source, output=smartcut['middle'][3], frametime=smartcut['middle'][0],
                                 duration=smartcut['middle'][2], allstreams=allstreams)
        if not middle_result:
            self.logger.error('smartcut error cutting MIDDLE clip')
        # 4. determine middle clip codecs
        smartcut_codec = self.codecs(smartcut['middle'][3])[0]
        # if smartcut_codec == 'h264':
        #     smartcut_codec = 'h264_nvenc'
        # 5. cut start and end clips using same codec as middle
        self.updateProgress.emit(2, '<b>SmartCut</b> : cut + encode START keyframe clip [2/5]...')
        start_result = self.cut(source=source, output=smartcut['start'][3], frametime=smartcut['start'][0],
                                duration=smartcut['start'][2], allstreams=allstreams, codecs=smartcut_codec, loglevel='info')
        if not start_result:
            self.logger.error('smartcut error cutting START clip')
        self.updateProgress.emit(3, '<b>SmartCut</b> : cut + encode END keyframe clip [3/5]...')
        end_result = self.cut(source=source, output=smartcut['end'][3], frametime=smartcut['end'][1],
                              duration=smartcut['end'][2], allstreams=allstreams, codecs=smartcut_codec, loglevel='info')
        if not end_result:
            self.logger.error('smartcut error cutting END clip')
        # 5. join three portions back together for our finalised smart cut clip
        self.updateProgress.emit(4, '<b>SmartCut</b> : joining START, MID and END [4/5]...')
        smartcut_join = [smartcut['start'][3], smartcut['middle'][3], smartcut['end'][3]]
        final_join = False
        if self.isMPEGcodec(smartcut['middle'][3]):
            self.logger.info('smartcut files are MPEG based so join via MPEG-TS')
            final_join = self.mpegtsJoin(smartcut_join, output)
        if not final_join:
            self.logger.info('smartcut MPEG-TS join failed, retry with standard concat')
            final_join = self.join(inputs=smartcut_join, output=output, allstreams=allstreams)
        # 6. cleanup files
        self.updateProgress.emit(5, '<b>SmartCut</b> : SUCCESS! Sanitize and clean up workspace [5/5]...')
        [os.remove(file) for file in smartcut_join]
        # 7. return all results for final assesment
        return start_result and middle_result and end_result and final_join

    def join(self, inputs: list, output: str, allstreams: bool=True) -> bool:
        self.checkDiskSpace(output)
        filelist = os.path.normpath(os.path.join(os.path.dirname(inputs[0]), '_vidcutter.list'))
        fobj = open(filelist, 'w')
        [fobj.write('file \'%s\'\n' % file.replace("'", "\\'")) for file in inputs]
        fobj.close()
        if allstreams:
            args = '-v error -f concat -safe 0 -i "{0}" -c copy -map 0 -y "{1}"'
        else:
            args = '-v error -f concat -safe 0 -i "{0}" -c copy -y "{1}"'
        result = self.cmdExec(self.backend, args.format(filelist, output))
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

    def getIDRFrames(self, source: str, formatted_time: bool=False) -> list:
        idrframes = list()
        args = '-v error -show_packets -select_streams v -show_entries packet=pts_time,flags {0}-of csv "{1}"' \
            .format('-sexagesimal ' if formatted_time else '', source)
        result = self.cmdExec(self.probe, args, output=True)
        for line in result.split('\n'):
            if re.search(',K', line):
                if formatted_time:
                    idrframes.append(line.split(',')[1][:-3])
                else:
                    idrframes.append(float(line.split(',')[1]))
        return idrframes

    def getGOPbisections(self, source: str, start: float, end: float) -> dict:
        idrtimes = self.getIDRFrames(source, formatted_time=False)
        start_pos = bisect_left(idrtimes, start)
        end_pos = bisect_left(idrtimes, end)
        return {
            'start': (idrtimes[start_pos - 1], idrtimes[start_pos], idrtimes[start_pos + 1]),
            'end': (idrtimes[end_pos - 2], idrtimes[end_pos - 1], idrtimes[end_pos])
        }

    def isMPEGcodec(self, source: str) -> bool:
        return self.codecs(source)[0].lower() in self.mpegCodecs

    # noinspection PyBroadException
    def mpegtsJoin(self, inputs: list, output: str) -> bool:
        result = False
        try:
            self.checkDiskSpace(output)
            outfiles = list()
            video_bsf, audio_bsf = self.getBSF(inputs[0])
            # 1. transcode to mpeg transport streams
            for file in inputs:
                name, _ = os.path.splitext(file)
                outfile = '%s.ts' % name
                outfiles.append(outfile)
                if os.path.isfile(outfile):
                    os.remove(outfile)
                args = '-v error -i "%s" -c copy -map 0 %s -f mpegts "%s"' % (file, video_bsf, outfile)
                if not self.cmdExec(self.backend, args):
                    return result
            # 2. losslessly concatenate at the file level
            if len(outfiles):
                if os.path.isfile(output):
                    os.remove(output)
                args = '-v error -i "concat:%s" -c copy %s "%s"' % ('|'.join(map(str, outfiles)), audio_bsf, output)
                result = self.cmdExec(self.backend, args)
                # 3. cleanup mpegts files
                [QFile.remove(file) for file in outfiles]
        except:
            self.logger.exception('Exception in VideoService.mpegtsJoin()', exc_info=True)
            result = False
        return result

    def version(self) -> str:
        args = '-version'
        result = self.cmdExec(self.backend, args, True)
        return re.search(r'ffmpeg\sversion\s([\S]+)\s', result).group(1)

    def metadata(self, source: str, output: str='HTML') -> str:
        args = '--output=%s "%s"' % (output, source)
        result = self.cmdExec(self.mediainfo, args, True)
        return result.strip()

    def cmdExec(self, cmd: str, args: str=None, output: bool=False):
        # if os.getenv('DEBUG', False):
        self.logger.info('"%s %s"' % (cmd, args if args is not None else ''))
        if self.proc.state() == QProcess.NotRunning:
            self.proc.setProcessChannelMode(QProcess.SeparateChannels if cmd == self.mediainfo
                                            else QProcess.MergedChannels)
            if cmd == self.backend:
                args = '-hide_banner {0}'.format(args)
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
