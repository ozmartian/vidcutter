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

import errno
import logging
import os
import re
import shlex
import sys
import traceback
from bisect import bisect_left
from distutils.spawn import find_executable
from enum import Enum
from functools import partial

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QDir, QFile, QFileInfo, QObject, QProcess, QProcessEnvironment,
                          QRunnable, QSize, QStorageInfo, QTemporaryFile, QThreadPool, QTime)
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QMessageBox

try:
    # noinspection PyPackageRequirements
    import simplejson as json
except ImportError:
    import json

from vidcutter.libs.munch import Munch
from vidcutter.libs.videoconfig import VideoConfig


class VideoService(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool)

    frozen = getattr(sys, 'frozen', False)
    spaceWarningThreshold = 200
    spaceWarningDelivered = False

    class ThumbSize(Enum):
        INDEX = QSize(100, 70)
        TIMELINE = QSize(80, 60)

    class Stream(Enum):
        AUDIO = 0
        VIDEO = 1
        SUBTITLE = 2

    config = VideoConfig()

    def __init__(self, parent=None):
        super(VideoService, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.backends = VideoService.findBackends()
        self.proc = VideoService.initProc()
        if hasattr(self.proc, 'errorOccurred'):
            self.proc.errorOccurred.connect(self.cmdError)
        self.lastError = ''
        self.media = None
        self.streams = Munch()
        self.threadpool = QThreadPool()

    def setMedia(self, source: str) -> None:
        try:
            self.probe(source)
            if self.media is not None:
                if os.getenv('DEBUG', False) or getattr(self.parent(), 'verboseLogs', False):
                    self.logger.info(self.media)
                for codec_type in VideoService.Stream.__members__:
                    setattr(self.streams, codec_type.lower(),
                            [stream for stream in self.media.streams if stream.codec_type == codec_type.lower()])
                self.streams.video = self.streams.video[0]
        except OSError as e:
            if e.errno == errno.ENOENT:
                errormsg = '{0}: {1}'.format(os.strerror(errno.ENOENT), source)
                self.logger.error(errormsg)
                raise FileNotFoundError(errormsg)

    @staticmethod
    def findBackends() -> Munch:
        tools = Munch(ffmpeg=None, ffprobe=None, mediainfo=None)
        for backend in tools.keys():
            for exe in VideoService.config.binaries[os.name][backend]:
                binpath = QDir.toNativeSeparators('{0}/bin/{1}'.format(QDir.currentPath(), exe))
                if os.path.isfile(binpath):
                    tools[backend] = binpath
                    break
                else:
                    binpath = find_executable(exe)
                    if os.path.isfile(binpath):
                        tools[backend] = binpath
                        break
        return tools

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
            warnmsg = 'There is less than {0}MB of disk space available at the target folder selected to save ' \
                      'your media. VidCutter WILL FAIL to produce your media if you run out of space during ' \
                      'operations.'
            QMessageBox.warning(self.parentWidget(), 'Disk space is low!',
                                warnmsg.format(VideoService.spaceWarningThreshold))
            self.spaceWarningDelivered = True

    @staticmethod
    def captureFrame(source: str, frametime: str, thumbsize: ThumbSize=ThumbSize.INDEX,
                     external: bool=False) -> QPixmap:
        capres = QPixmap()
        img = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX.jpg'))
        if img.open():
            imagecap = img.fileName()
            size = thumbsize.value
            cmd = VideoService.findBackends().ffmpeg
            args = '-hide_banner -ss %s -i "%s" -vframes 1 -s %ix%i -y "%s"' % (frametime, source, size.width(),
                                                                                size.height(), imagecap)
            proc = VideoService.initProc()
            proc.setProcessChannelMode(QProcess.MergedChannels)
            if proc.state() == QProcess.NotRunning:
                if os.getenv('DEBUG', False):
                    logging.getLogger(__name__).info('"%s %s"' % (cmd, args))
                proc.start(cmd, shlex.split(args))
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
            VideoService.cleanup([file1_cut.fileName(), file2_cut.fileName(), final_join.fileName()])
        except:
            self.logger.exception('Exception in VideoService.testJoin', exc_info=True)
            result = False
        return result

    def framesize(self, source: str=None) -> QSize:
        if source is None and len(self.streams.video):
            return QSize(int(self.streams.video.width), int(self.streams.video.height))
        else:
            args = '-i "%s"' % source
            result = self.cmdExec(self.backends.ffmpeg, args, True)
            matches = re.search(r'Stream.*Video:.*[,\s](?P<width>\d+?)x(?P<height>\d+?)[,\s]',
                                result, re.DOTALL).groupdict()
            return QSize(int(matches['width']), int(matches['height']))

    def duration(self, source: str=None) -> QTime:
        if source is None and hasattr(self.media, 'format') and self.parent() is not None:
            return self.parent().delta2QTime(float(self.media.format.duration) * 1000)
        else:
            args = '-i "%s"' % source
            result = self.cmdExec(self.backends.ffmpeg, args, True)
            matches = re.search(r'Duration:\s(?P<hrs>\d+?):(?P<mins>\d+?):(?P<secs>\d+\.\d+?),',
                                result, re.DOTALL).groupdict()
            secs, msecs = matches['secs'].split('.')
            return QTime(int(matches['hrs']), int(matches['mins']), int(secs), int(msecs))

    def codecs(self, source: str=None) -> tuple:
        if source is None and len(self.streams.video):
            return self.streams.video.codec_name, self.streams.audio[0].codec_name if len(self.streams.audio) else None
        else:
            args = '-i "%s"' % source
            result = self.cmdExec(self.backends.ffmpeg, args, True)
            vcodec = re.search(r'Stream.*Video:\s(\w+)', result).group(1)
            acodec = re.search(r'Stream.*Audio:\s(\w+)', result).group(1)
            return vcodec, acodec

    def cut(self, source: str, output: str, frametime: str, duration: str, allstreams: bool=True,
            vcodec: str=None, loglevel: str='error', run: bool=True):
        self.checkDiskSpace(output)
        stream_map = '-map 0 ' if allstreams else ''
        if vcodec is not None:
            encode_settings = VideoService.encodeSettings(vcodec)
            args = '-v {loglevel} -i "{source}" -ss {frametime} -t {duration} -c:v {encode_settings} ' \
                   '-c:a copy -c:s copy {stream_map}-y "{output}"'.format(**locals())
        else:
            args = '-v {loglevel} -ss {frametime} -i "{source}" -t {duration} -c copy {stream_map}' \
                   '-avoid_negative_ts 1 -copyinkf -y "{output}"'.format(**locals())
        if run:
            return self.cmdExec(self.backends.ffmpeg, args)
        else:
            return self.backends.ffmpeg, args

    @staticmethod
    def encodeSettings(codec: str) -> str:
        encoding = {
            'hevc': 'libx265 -tune zerolatency -preset ultrafast -x265-params crf=20 -qp 4',
            'h264': 'libx264 -tune film -preset ultrafast -x264-params crf=20 -qp 0',
            'vp9': 'libvpx-vp9 -deadline best -quality best'
        }
        return encoding.get(codec, codec)

    def smartcut(self, source: str, output: str, start: float, end: float, allstreams: bool=True) -> None:
        output_file, output_ext = os.path.splitext(source)
        # get GOP bisections for start and end of clip times to be reencoded for frame accurate cuts
        # smartcut -> list: start, end, duration, filename
        bisections = self.getGOPbisections(source, start, end)
        smartcut_files = [
            '{0}_start{1}'.format(output_file, output_ext),
            '{0}_middle{1}'.format(output_file, output_ext),
            '{0}_end{1}'.format(output_file, output_ext)
        ]
        smartcut_progress = [
            '<b>SmartCut [1/5] :</b> cutting main video chunk...',
            '<b>SmartCut [2/5] :</b> cut + encode START keyframe clip...',
            '<b>SmartCut [3/5] :</b> cut + encode END keyframe clip...'
        ]
        smartcut_cmds = [
            self.cut(source=source,
                     output=smartcut_files[1],
                     frametime=bisections['start'][2],
                     duration=bisections['end'][1] - bisections['start'][2],
                     allstreams=allstreams,
                     run=False),
            self.cut(source=source,
                     output=smartcut_files[0],
                     frametime=str(start),
                     duration=bisections['start'][1] - start,
                     allstreams=allstreams,
                     vcodec=self.streams.video.codec_name,
                     loglevel='info',
                     run=False),
            self.cut(source=source,
                     output=smartcut_files[2],
                     frametime=bisections['end'][1],
                     duration=end - bisections['end'][1],
                     allstreams=allstreams,
                     vcodec=self.streams.video.codec_name,
                     loglevel='info',
                     run=False)
        ]
        worker = VideoWorker(smartcut_cmds, smartcut_progress,
                             os.getenv('DEBUG', False) or getattr(self.parent(), 'verboseLogs', False))
        worker.signals.progress.connect(self.progress)
        worker.signals.result.connect(lambda results: self.smartjoin(output, smartcut_files, results, allstreams))
        worker.signals.error.connect(lambda errortuple: VideoService.cleanup(smartcut_files))
        self.threadpool.start(worker)

    @pyqtSlot(str, list, list, bool)
    def smartjoin(self, output: str, files: list, results: list, allstreams: bool) -> None:
        if False in results:
            return
        self.progress.emit('<b>SmartCut [4/5] :</b> joining START, MID and END...')
        final_join = False
        if self.isMPEGcodec(files[1]):
            self.logger.info('smartcut files are MPEG based so join via MPEG-TS')
            final_join = self.mpegtsJoin(files, output)
        if not final_join:
            self.logger.info('smartcut MPEG-TS join failed, retry with standard concat')
            final_join = self.join(inputs=files, output=output, allstreams=allstreams)
        self.progress.emit('<b>SmartCut [5/5] :</b> Complete! Sanitize and clean up workspace...')
        VideoService.cleanup(files)

        exectime = self.parent.cuttimer.elapsed()
        del self.parent.cuttimer
        print('cut execution time: {}'
              .format(self.parent.delta2QTime(exectime).toString(self.parent.timeformat)))

        results.append(final_join)
        self.finished.emit(False not in results)

    @staticmethod
    def cleanup(files: list) -> None:
        [os.remove(file) for file in files]

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
        result = self.cmdExec(self.backends.ffmpeg, args.format(filelist, output))
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

    def probe(self, source: str) -> bool:
        try:
            args = '-v error -show_streams -show_format -of json "{0}"'.format(source)
            json_data = self.cmdExec(self.backends.ffprobe, args, output=True)
            self.media = Munch.fromDict(json.loads(json_data))
            return hasattr(self.media, 'streams') and len(self.media.streams)
        except FileNotFoundError:
            self.logger.exception('Probe media file not found: {0}'.format(source), exc_info=True)
            raise
        except json.JSONDecodeError:
            self.logger.exception('Error decoding ffprobe JSON output', exc_info=True)
            raise

    def getIDRFrames(self, source: str, formatted_time: bool=False) -> list:
        idrframes = list()
        args = '-v error -show_packets -select_streams v -show_entries packet=pts_time,flags {0}-of csv "{1}"' \
            .format('-sexagesimal ' if formatted_time else '', source)
        result = self.cmdExec(self.backends.ffprobe, args, output=True)
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

    def isMPEGcodec(self, source: str=None) -> bool:
        if source is None and len(self.streams.video):
            codec = self.streams.video.codec_name
        else:
            codec = self.codecs(source)[0].lower()
        return codec in VideoService.config.mpeg_formats

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
                if not self.cmdExec(self.backends.ffmpeg, args):
                    return result
            # 2. losslessly concatenate at the file level
            if len(outfiles):
                if os.path.isfile(output):
                    os.remove(output)
                args = '-v error -i "concat:%s" -c copy %s "%s"' % ('|'.join(map(str, outfiles)), audio_bsf, output)
                result = self.cmdExec(self.backends.ffmpeg, args)
                # 3. cleanup mpegts files
                [QFile.remove(file) for file in outfiles]
        except:
            self.logger.exception('Exception during MPEG-TS join', exc_info=True)
            result = False
        return result

    def version(self) -> str:
        args = '-version'
        result = self.cmdExec(self.backends.ffmpeg, args, True)
        return re.search(r'ffmpeg\sversion\s([\S]+)\s', result).group(1)

    def mediainfo(self, source: str, output: str='HTML') -> str:
        args = '--output=%s "%s"' % (output, source)
        result = self.cmdExec(self.backends.mediainfo, args, True)
        return result.strip()

    def cmdExec(self, cmd: str, args: str=None, output: bool=False):
        if os.getenv('DEBUG', False) or getattr(self.parent(), 'verboseLogs', False):
            self.logger.info('{0} {1}'.format(cmd, args if args is not None else ''))
        if self.proc.state() == QProcess.NotRunning:
            self.proc.setProcessChannelMode(QProcess.SeparateChannels if cmd == self.backends.mediainfo
                                            else QProcess.MergedChannels)
            if cmd == self.backends.ffmpeg:
                args = '-hide_banner {}'.format(args)
            self.proc.start(cmd, shlex.split(args))
            self.proc.readyReadStandardOutput.connect(
                partial(self.cmdOut, self.proc.readAllStandardOutput().data().decode().strip()))
            self.proc.waitForFinished(-1)
            if output:
                cmdoutput = self.proc.readAllStandardOutput().data().decode()
                if os.getenv('DEBUG', False):
                    self.logger.info('cmd output: {0}'.format(cmdoutput))
                return cmdoutput
            return self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0
        return False

    @pyqtSlot(str)
    def cmdOut(self, output: str) -> None:
        if len(output):
            self.logger.info(output)

    @pyqtSlot(QProcess.ProcessError)
    def cmdError(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.Crashed:
            QMessageBox.critical(self.parentWidget(), '',
                                 '<h4>%s Error:</h4>' % self.backends.ffmpeg +
                                 '<p>%s</p>' % self.proc.errorString(), buttons=QMessageBox.Close)

    # noinspection PyUnresolvedReferences, PyProtectedMember
    @staticmethod
    def getAppPath() -> str:
        if VideoService.frozen:
            return sys._MEIPASS
        return QFileInfo(__file__).absolutePath()


class VideoSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(list)
    progress = pyqtSignal(str)


class VideoWorker(QRunnable):
    def __init__(self, cmds: list, progresstxt: list, uselog: bool=False):
        super(VideoWorker, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.cmds = cmds
        self.progresstxt = progresstxt
        self.uselog = uselog
        self.signals = VideoSignals()
        self.proc = QProcess()
        self.proc.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        self.proc.setWorkingDirectory(VideoService.getAppPath())

    def run(self):
        results = []
        # noinspection PyBroadException
        try:
            if self.proc.state() == QProcess.NotRunning:
                self.proc.setProcessChannelMode(QProcess.MergedChannels)
                for cmd, args in self.cmds:
                    index = self.cmds.index((cmd, args))
                    if self.uselog:
                        self.logger.info('{0} {1}'.format(cmd, args))
                    self.signals.progress.emit(self.progresstxt[index])
                    self.proc.start(cmd, shlex.split('-hide_banner {0}'.format(args)))
                    self.proc.waitForFinished(-1)
                    results.append(self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(results)
        finally:
            self.signals.finished.emit()
