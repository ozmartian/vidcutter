#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
#
# copyright © 2018 Pete Alexandrou
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
import sys
from bisect import bisect_left, bisect_right
from functools import partial
from typing import Dict, List, Optional, Tuple, Union

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QDir, QFileInfo, QObject, QProcess, QProcessEnvironment, QSettings,
                          QSize, QStandardPaths, QStorageInfo, QTemporaryFile, QTime)
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QMessageBox, QWidget

from vidcutter.libs.config import Config, InvalidMediaException, Streams, ToolNotFoundException
from vidcutter.libs.ffmetadata import FFMetadata
from vidcutter.libs.munch import Munch
from vidcutter.libs.widgets import VCMessageBox

try:
    # noinspection PyPackageRequirements
    from simplejson import loads, JSONDecodeError
except ImportError:
    from json import loads, JSONDecodeError


class VideoService(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    error = pyqtSignal(str)
    addScenes = pyqtSignal(list)

    frozen = getattr(sys, 'frozen', False)
    spaceWarningThreshold = 200
    spaceWarningDelivered = False
    smartcutError = False

    config = Config()

    def __init__(self, settings: QSettings, parent: QWidget):
        super(VideoService, self).__init__(parent)
        self.settings = settings
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        try:
            self.backends = VideoService.findBackends(self.settings)
            self.proc = VideoService.initProc()
            if hasattr(self.proc, 'errorOccurred'):
                self.proc.errorOccurred.connect(self.cmdError)
            self.lastError = ''
            self.media, self.source = None, None
            self.chapter_metadata = None
            self.keyframes = []
            self.streams = Munch()
            self.mappings = []
        except ToolNotFoundException as e:
            self.logger.exception(e.msg, exc_info=True)
            QMessageBox.critical(getattr(self, 'parent', None), 'Missing libraries', e.msg)

    def setMedia(self, source: str) -> None:
        try:
            self.source = QDir.toNativeSeparators(source)
            self.media = self.probe(source)
            if self.media is not None:
                if getattr(self.parent, 'verboseLogs', False):
                    self.logger.info(self.media)
                for codec_type in Streams.__members__:
                    setattr(self.streams, codec_type.lower(),
                            [stream for stream in self.media.streams
                             if hasattr(stream, 'codec_type') and stream.codec_type == codec_type.lower()])
                if len(self.streams.video):
                    self.streams.video = self.streams.video[0]  # we always assume one video stream per media file
                else:
                    raise InvalidMediaException('Could not load video stream for {}'.format(source))
                self.mappings.clear()
                # noinspection PyUnusedLocal
                [self.mappings.append(True) for i in range(int(self.media.format.nb_streams))]
        except OSError as e:
            if e.errno == errno.ENOENT:
                errormsg = '{0}: {1}'.format(os.strerror(errno.ENOENT), source)
                self.logger.error(errormsg)
                raise FileNotFoundError(errormsg)

    @staticmethod
    def findBackends(settings: QSettings) -> Munch:
        tools = Munch(ffmpeg=None, ffprobe=None, mediainfo=None)
        settings.beginGroup('tools')
        tools.ffmpeg = settings.value('ffmpeg', None, type=str)
        tools.ffprobe = settings.value('ffprobe', None, type=str)
        tools.mediainfo = settings.value('mediainfo', None, type=str)
        for tool, path in tools.items():
            if path is None or not len(path) or not os.path.isfile(path):
                for exe in VideoService.config.binaries[os.name][tool]:
                    if VideoService.frozen:
                        binpath = VideoService.getAppPath(os.path.join('bin', exe))
                    else:
                        binpath = QStandardPaths.findExecutable(exe)
                        if not len(binpath):
                            binpath = QStandardPaths.findExecutable(exe, [VideoService.getAppPath('bin')])
                    if os.path.isfile(binpath) and os.access(binpath, os.X_OK):
                        tools[tool] = binpath
                        if not VideoService.frozen:
                            settings.setValue(tool, binpath)
                        break
        settings.endGroup()
        if tools.ffmpeg is None:
            raise ToolNotFoundException('FFmpeg missing')
        if tools.ffprobe is None:
            raise ToolNotFoundException('FFprobe missing')
        if tools.mediainfo is None:
            raise ToolNotFoundException('MediaInfo missing')
        return tools

    @staticmethod
    def initProc(program: str=None, finish: pyqtSlot=None, workingdir: str=None) -> QProcess:
        p = QProcess()
        p.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        p.setProcessChannelMode(QProcess.MergedChannels)
        if workingdir is not None:
            p.setWorkingDirectory(workingdir)
        if program is not None:
            p.setProgram(program)
        if finish is not None:
            p.finished.connect(finish)
        return p

    def checkDiskSpace(self, path: str) -> None:
        # noinspection PyCallByClass
        if self.spaceWarningDelivered or not QFileInfo.exists(path):
            return
        info = QStorageInfo(path)
        available = info.bytesAvailable() / 1000 / 1000
        if available < VideoService.spaceWarningThreshold:
            warnmsg = 'There is less than {}MB of free disk space in the '.format(VideoService.spaceWarningThreshold)
            warnmsg += 'folder selected to save your media. '
            warnmsg += 'VidCutter will fail if space runs out before processing completes.'
            spacewarn = VCMessageBox('Warning', 'Disk space alert', warnmsg, self.parentWidget())
            spacewarn.addButton(VCMessageBox.Ok)
            spacewarn.exec_()
            self.spaceWarningDelivered = True

    @staticmethod
    def captureFrame(settings: QSettings, source: str, frametime: str, thumbsize: QSize=None,
                     external: bool=False) -> QPixmap:
        if thumbsize is None:
            thumbsize = VideoService.config.thumbnails['INDEX']
        capres = QPixmap()
        img = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX.jpg'))
        if img.open():
            imagecap = img.fileName()
            cmd = VideoService.findBackends(settings).ffmpeg
            tsize = '{0:d}x{1:d}'.format(thumbsize.width(), thumbsize.height())
            args = [
                '-hide_banner',
                '-ss', frametime,
                '-i', source,
                '-vframes', '1',
                '-s', tsize,
                '-y', imagecap,
            ]
            proc = VideoService.initProc()
            if proc.state() == QProcess.NotRunning:
                proc.start(cmd, args)
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
        self.logger.info('attempting to test joining of "{0}" & "{1}"'.format(file1, file2))
        try:
            # 1. check audio + video codecs
            file1_codecs = self.codecs(file1)
            file2_codecs = self.codecs(file2)
            if file1_codecs != file2_codecs:
                self.logger.info('join test failed for {0} and {1}: codecs mismatched'.format(file1, file2))
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
                self.logger.info('join test failed for {0} and {1}: frame size mismatched'.format(file1, file2))
                self.lastError = '<p>The frame size of this media file is not the same as the files already in ' \
                                 'your clip index.</p>' \
                                 '<div align="center">Current media clips are <b>{0}x{1}</b>' \
                                 '<br/>Failed media file is <b>{2}x{3}</b></div>'
                self.lastError = self.lastError.format(size1.width(), size1.height(), size2.width(), size2.height())
                return result
            # 2. generate temporary file handles
            _, ext = os.path.splitext(file1)
            file1_cut = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX{}'.format(ext)))
            file2_cut = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX{}'.format(ext)))
            final_join = QTemporaryFile(os.path.join(QDir.tempPath(), 'XXXXXX{}'.format(ext)))
            # 3. produce 4 secs clips from input files for join test
            if file1_cut.open() and file2_cut.open() and final_join.open():
                result1 = self.cut(file1, file1_cut.fileName(), '00:00:00.000', '00:00:04.00', False)
                result2 = self.cut(file2, file2_cut.fileName(), '00:00:00.000', '00:00:04.00', False)
                if result1 and result2:
                    # 4. attempt join of temp 2 second clips
                    result = self.join([file1_cut.fileName(), file2_cut.fileName()],
                                       final_join.fileName(), False, None)
            VideoService.cleanup([file1_cut.fileName(), file2_cut.fileName(), final_join.fileName()])
        except BaseException:
            self.logger.exception('Exception in VideoService.testJoin', exc_info=True)
            result = False
        return result

    def framesize(self, source: str = None) -> QSize:
        if source is None and hasattr(self.streams, 'video'):
            return QSize(int(self.streams.video.width), int(self.streams.video.height))
        else:
            args = ['-i', source]
            result = self.cmdExec(self.backends.ffmpeg, args, True)
            matches = re.search(r'Stream.*Video:.*[,\s](?P<width>\d+?)x(?P<height>\d+?)[,\s]',
                                result, re.DOTALL).groupdict()
            return QSize(int(matches['width']), int(matches['height']))

    def duration(self, source: str = None) -> QTime:
        if source is None and hasattr(self.media, 'format') and self.parent is not None:
            return self.parent.delta2QTime(float(self.media.format.duration))
        else:
            args = ['-i', source]
            result = self.cmdExec(self.backends.ffmpeg, args, True)
            matches = re.search(r'Duration:\s(?P<hrs>\d+?):(?P<mins>\d+?):(?P<secs>\d+\.\d+?),',
                                result, re.DOTALL).groupdict()
            secs, msecs = matches['secs'].split('.')
            return QTime(int(matches['hrs']), int(matches['mins']), int(secs), int(msecs))

    def durationSecs(self, source: str = None) -> float:
        if source is None and hasattr(self.media, 'format') and self.parent is not None:
            return float(self.media.format.duration)
        else:
            args = ['-i', source]
            result = self.cmdExec(self.backends.ffmpeg, args, True)
            matches = re.search(r'Duration:\s(?P<hrs>\d+?):(?P<mins>\d+?):(?P<secs>\d+\.\d+?),',
                                result, re.DOTALL).groupdict()
            secs, msecs = matches['secs'].split('.')
            return int(matches['hrs'])*3600 + int(matches['mins'])*60 + int(secs) + int(msecs) / 1000

    def qTime2float(self, qTime : QTime) -> float:
        return qTime.hour()*3600 + qTime.minute()*60 + qTime.second() + qTime.msec() / 1000

    def codecs(self, source: str = None) -> tuple:
        if source is None and hasattr(self.streams, 'video'):
            return self.streams.video.codec_name, self.streams.audio[0].codec_name if len(self.streams.audio) else None
        else:
            args = ['-i', source]
            result = self.cmdExec(self.backends.ffmpeg, args, True)
            match = re.search(r'Stream.*Video:\s(\w+)', result)
            if match:
                vcodec = match.group(1)
            else:
                vcodec = None
            match = re.search(r'Stream.*Audio:\s(\w+)', result)
            if match:
                acodec = match.group(1)
            else:
                acodec = None
            return vcodec, acodec

    def parseMappings(self, allstreams: bool = True) -> List[str]:
        if not len(self.mappings) or (self.parent is not None and self.parent.hasExternals()):
            return ['-map', '0'] if allstreams else []
        # if False not in self.mappings:
        #     return '-map 0 '
        output = []
        for stream_id, stream in enumerate(self.mappings):
            if stream:
                output += ['-map', '0:{}'.format(stream_id)]
        return output

    def finalize(self, source: str) -> bool:
        self.checkDiskSpace(source)
        source_file, source_ext = os.path.splitext(source)
        final_filename = '{0}_FINAL{1}'.format(source_file, source_ext)
        args = [
            '-v', 'error',
            '-i', source,
            '-map', '0',
            '-c', 'copy',
            '-y', final_filename,
        ]
        result = self.cmdExec(self.backends.ffmpeg, args)
        if result and os.path.exists(final_filename):
            os.replace(final_filename, source)
            return True
        return False

    def cut(self, source: str, output: str, frametime: str, duration: str, allstreams: bool=True, vcodec: str=None,
            run: bool=True, seektime: str=None) -> Union[bool, List[str]]:
        self.checkDiskSpace(output)
        stream_map = self.parseMappings(allstreams)
        if vcodec is not None:
            encode_options = VideoService.config.encoding.get(vcodec, ['copy'])
            args = [
                '-v', 'info',
                '-i', source,
                '-ss', frametime,
                '-t', duration,
                '-c:v',
            ] + encode_options + [
                '-c:a', 'copy',
                '-c:s', 'copy',
            ] + stream_map + [
                '-avoid_negative_ts', '1',
                '-y', output,
            ]
        else:
            args = [
                '-v', 'error',
                '-i', source,
                '-ss', frametime,
                '-t', duration,
                '-c', 'copy',
            ] + stream_map + [
                '-avoid_negative_ts', '1',
                '-y', output,
            ]
        if seektime is not None:
            # insert seektime before '-i'
            idx = args.index('-i')
            args[idx:idx] = ['-ss', seektime]
        if run:
            result = self.cmdExec(self.backends.ffmpeg, args)
            if not result or os.path.getsize(output) < 1000:
                if allstreams:
                    # cut failed so try again without mapping all media streams
                    self.logger.info('cut resulted in zero length file, trying again without all stream mapping')
                    self.cut(source, output, frametime, duration, False)
                else:
                    # both attempts to cut have failed so exit and let user know
                    VideoService.cleanup([output])
                    return False
            return True
        else:
            if os.getenv('DEBUG', False) or getattr(self.parent, 'verboseLogs', False):
                self.logger.info(' '.join([self.backends.ffmpeg] + args))
            return args

    def smartinit(self, clips: int):
        self.smartcut_jobs = []
        # noinspection PyUnusedLocal
        [
            self.smartcut_jobs.append(Munch(output='', bitrate=0, allstreams=True, procs={}, files={}, results={}))
            for index in range(clips)
        ]

    def smartcut(self, index: int, source: str, output: str, start: float, end: float, keyframes: [], allstreams: bool = True) -> None:
        output_file, output_ext = os.path.splitext(output)
        bisections = self.getGOPbisections(keyframes, start, end)
        self.smartcut_jobs[index].output = output
        self.smartcut_jobs[index].allstreams = allstreams
        # ----------------------[ STEP 1 - start of clip if not starting on a keyframe ]-------------------------
        if start == bisections['start'][1]:
            vcodec = None # copy
        else:
            vcodec = self.streams.video.codec_name # re-encode
        self.smartcut_jobs[index].files.update(start='{0}_start_{1}{2}'
                                               .format(output_file, '{0:0>2}'.format(index), output_ext))
        startproc = VideoService.initProc(self.backends.ffmpeg, self.smartcheck, os.path.dirname(source))
        startproc.setObjectName('start.{}'.format(index))
        startproc.started.connect(lambda: self.progress.emit(index))
        dur=round(bisections['start'][2] - start, 6)
        startproc.setArguments(
            self.cut(source=source,
                     output=self.smartcut_jobs[index].files['start'],
                     seektime=str(bisections['start'][0]),
                     frametime=str(round(start - bisections['start'][0], 6)),
                     duration=str(dur),
                     allstreams=allstreams,
                     vcodec=vcodec,
                     run=False))
        self.smartcut_jobs[index].procs.update(start=startproc)
        self.smartcut_jobs[index].results.update(start=False)
        startproc.start()
        # ----------------------[ STEP 2 - cut middle segment of clip ]-------------------------
        self.smartcut_jobs[index].files.update(middle='{0}_middle_{1}{2}'
                                               .format(output_file, '{0:0>2}'.format(index), output_ext))
        middleproc = VideoService.initProc(self.backends.ffmpeg, self.smartcheck, os.path.dirname(source))
        middleproc.setProcessChannelMode(QProcess.MergedChannels)
        middleproc.setWorkingDirectory(os.path.dirname(self.smartcut_jobs[index].files['middle']))
        middleproc.setObjectName('middle.{}'.format(index))
        middleproc.started.connect(lambda: self.progress.emit(index))
        dur=round(bisections['end'][1] - bisections['start'][2], 6)
        middleproc.setArguments(
            self.cut(source=source,
                     output=self.smartcut_jobs[index].files['middle'],
                     seektime=str(bisections['start'][1]),
                     frametime=str(round(bisections['start'][2] - bisections['start'][1], 6)),
                     duration=str(dur),
                     allstreams=allstreams,
                     run=False))
        self.smartcut_jobs[index].procs.update(middle=middleproc)
        self.smartcut_jobs[index].results.update(middle=False)
        if len(self.smartcut_jobs[index].procs) == 1:
            middleproc.start()
        # ----------------------[ STEP 3 - end of clip if not ending on a keyframe ]-------------------------
        if end == bisections['end'][2]:
            vcodec = None # copy
        else:
            vcodec = self.streams.video.codec_name # re-encode
        self.smartcut_jobs[index].files.update(end='{0}_end_{1}{2}'
                                               .format(output_file, '{0:0>2}'.format(index), output_ext))
        endproc = VideoService.initProc(self.backends.ffmpeg, self.smartcheck, os.path.dirname(source))
        endproc.setObjectName('end.{}'.format(index))
        endproc.started.connect(lambda: self.progress.emit(index))
        dur=round(end - bisections['end'][1], 6)
        endproc.setArguments(
            self.cut(source=source,
                     output=self.smartcut_jobs[index].files['end'],
                     seektime=str(bisections['end'][0]),
                     frametime=str(round(bisections['end'][1] - bisections['end'][0], 6)),
                     duration=str(dur),
                     allstreams=allstreams,
                     vcodec=vcodec,
                     run=False))
        self.smartcut_jobs[index].procs.update(end=endproc)
        self.smartcut_jobs[index].results.update(end=False)
        endproc.start()


    def forceKeyframes(self, source: str, clipTimes: [], fps: float, output: str) -> None:
        # stream_map = self.parseMappings(true)
        #eq(n,45)+eq(n,99)+eq(n,154)'
        # forcedKeyframes = toFrames(clipTimes)
        keyframesExpr = 'expr:'
        for index, clip in enumerate(clipTimes):
            # if index == 0 and clip[0] != 0:
            #     keyframesExpr += f'eq(n,{self.qTime2float(clip[0])*fps})'
            # else:
            keyframesExpr += f'eq(n,{int(self.qTime2float(clip[0])*fps)})'
            keyframesExpr += '+'
            keyframesExpr += f'eq(n,{int(self.qTime2float(clip[1])*fps)})'
            keyframesExpr += '+'
        keyframesExpr = keyframesExpr[:-1]
        args = [
                '-v', 'info',
                '-i', source,
                '-map','0',
                '-c','copy',
                '-force_key_frames', keyframesExpr,
                '-y', output,
            ]
        # print(args)
        if os.path.isfile(output):
                os.remove(output)
        if not self.cmdExec(self.backends.ffmpeg, args):
            return result

    @pyqtSlot(int, QProcess.ExitStatus)
    def smartcheck(self, code: int, status: QProcess.ExitStatus) -> None:
        if hasattr(self, 'smartcut_jobs') and not self.smartcutError:
            name, index = self.sender().objectName().split('.')
            index = int(index)
            self.smartcut_jobs[index].results[name] = (code == 0 and status == QProcess.NormalExit)
            if os.getenv('DEBUG', False) or getattr(self.parent, 'verboseLogs', False):
                self.logger.info('SmartCut progress for part {0}: {1}'.format(index, self.smartcut_jobs[index].results))
            resultfile = self.smartcut_jobs[index].files.get(name)
            if not self.smartcut_jobs[index].results[name] or os.path.getsize(resultfile) < 1000:
                args = self.smartcut_jobs[index].procs[name].arguments()
                if '-map' in args:
                    self.logger.info('SmartCut resulted in zero length file, trying again without all stream mapping')
                    pos = args.index('-map')
                    args.remove('-map')
                    del args[pos]
                    self.smartcut_jobs[index].procs[name].setArguments(args)
                    try:
                        self.smartcut_jobs[index].procs[name].started.disconnect()
                    except TypeError as e:
                        self.logger.exception('Failed to disconnect SmartCut job {0}.'.format(name), exc_info=True)
                    self.smartcut_jobs[index].procs[name].start()
                    return
                else:
                    self.smartcutError = True
                    # both attempts to cut have failed so exit and let user know
                    self.logger.error('Error executing: {0} {1}'
                                      .format(self.smartcut_jobs[index].procs[name].program(), args))
                    self.error.emit('SmartCut failed to cut media file. Please ensure your media files are valid '
                                    'otherwise try again with SmartCut disabled.')
                    return
            if False not in self.smartcut_jobs[index].results.values():
                self.smartjoin(index)
            else:
                if name == 'start':
                    self.smartcut_jobs[index].procs['middle'].start()
                elif name == 'middle':
                    self.smartcut_jobs[index].procs['end'].start()

    def smartabort(self):
        for job in self.smartcut_jobs:
            for name in job.procs:
                if job.procs[name].state() != QProcess.NotRunning:
                    job.procs[name].terminate()
            VideoService.cleanup(job.files)

    def smartjoin(self, index: int) -> None:
        self.progress.emit(index)
        final_join = False
        joinlist = [
            self.smartcut_jobs[index].files.get('start'),
            self.smartcut_jobs[index].files.get('middle'),
            self.smartcut_jobs[index].files.get('end')
        ]
        if self.isMPEGcodec(joinlist[1]):
            self.logger.info('smartcut files are MPEG based so join via MPEG-TS')
            final_join = self.mpegtsJoin(joinlist, self.smartcut_jobs[index].output, None)
        if not final_join:
            self.logger.info('smartcut MPEG-TS join failed, retry with standard concat')
            final_join = self.join(joinlist, self.smartcut_jobs[index].output,
                                   self.smartcut_jobs[index].allstreams, None)
        VideoService.cleanup(joinlist)
        self.finished.emit(final_join, self.smartcut_jobs[index].output)

    @staticmethod
    def cleanup(files: List[str]) -> None:
        try:
            [os.remove(file) for file in files if file]
        except (FileNotFoundError, TypeError):
            pass

    def join(self, inputs: List[str], output: str, allstreams: bool=True, chapters: Optional[List[str]]=None) -> bool:
        self.checkDiskSpace(output)
        filelist = os.path.normpath(os.path.join(os.path.dirname(inputs[0]), '_vidcutter.list'))
        with open(filelist, 'w') as f:
            [f.write('file \'{}\'\n'.format(file.replace("'", "\\'"))) for file in inputs]
        stream_map = ['-map', '0'] if allstreams else []
        ffmetadata = None
        if chapters is not None and len(chapters):
            ffmetadata = self.getChapterFile(inputs, chapters)
            metadata = ['-i', ffmetadata, '-map_metadata', '1']
        else:
            metadata = []
        args = [
            '-v', 'error',
            '-f', 'concat',
            '-safe', '0',
            '-i', filelist,
        ] + metadata + [
            '-c', 'copy',
        ] + stream_map + [
            '-y', output,
        ]
        result = self.cmdExec(self.backends.ffmpeg, args)
        os.remove(filelist)
        if chapters and ffmetadata is not None:
            os.remove(ffmetadata)
        return result

    def getChapterFile(self, scenes: List[str], titles: List[str]=None) -> str:
        ffmetadata = FFMetadata()
        pos = 0
        for index, scene in enumerate(scenes):
            duration = self.duration(scene)
            end = pos + duration.msecsSinceStartOfDay()
            ffmetadata.add_chapter(pos, end, titles[index])
            pos = end
        ffmetafile = os.path.normpath(os.path.join(os.path.dirname(scenes[0]), 'ffmetadata.txt'))
        with open(ffmetafile, 'w') as f:
            f.write(ffmetadata.output())
        return ffmetafile

    def getBSF(self, source: str) -> tuple:
        vbsf, absf = '', ''
        vcodec, acodec = self.codecs(source)
        if vcodec:
            prefix = '-bsf:v'
            if vcodec == 'hevc':
                vbsf = '{} hevc_mp4toannexb'.format(prefix)
            elif vcodec == 'h264':
                vbsf = '{} h264_mp4toannexb'.format(prefix)
            elif vcodec == 'mpeg4':
                vbsf = '{} mpeg4_unpack_bframes'.format(prefix)
            elif vcodec in {'webm', 'ivf', 'vp9'}:
                vbsf = '{} vp9_superframe'.format(prefix)
        if acodec:
            prefix = '-bsf:a'
            if acodec == 'aac':
                absf = '{} aac_adtstoasc'.format(prefix)
            elif acodec == 'mp3':
                absf = '{} mp3decomp'.format(prefix)
        return vbsf, absf

    def blackdetect(self, min_duration: float) -> None:
        try:
            args = [
                '-f', 'lavfi',
                '-i', 'movie={0},blackdetect=d={1:.1f}[out0]'.format(os.path.basename(self.source), min_duration),
                '-show_entries', 'tags=lavfi.black_start,lavfi.black_end',
                '-of', 'default=nw=1',
                '-hide_banner',
            ]
            if os.getenv('DEBUG', False) or getattr(self.parent, 'verboseLogs', False):
                self.logger.info('{0} {1}'.format(self.backends.ffprobe, ' '.join(args)))
            self.filterproc = VideoService.initProc(self.backends.ffprobe, lambda: self.on_blackdetect(min_duration),
                                                    os.path.dirname(self.source))
            self.filterproc.setArguments(args)
            self.filterproc.start()
        except FileNotFoundError:
            self.logger.exception('Could not find media file: {}'.format(self.source), exc_info=True)
            raise

    def on_blackdetect(self, min_duration: float) -> None:
        if self.filterproc.exitStatus() == QProcess.NormalExit and self.filterproc.exitCode() == 0:
            scenes = [[QTime(0, 0)]]
            results = self.filterproc.readAllStandardOutput().data().decode('iso-8859-1').strip()
            for line in results.split('\n'):
                if re.match(r'\[blackdetect @ (.*)\]', line):
                    vals = line.split(']')[1].strip().split(' ')
                    start = float(vals[0].replace('black_start:', ''))
                    end = float(vals[1].replace('black_end:', ''))
                    dur = float(vals[2].replace('black_duration:', ''))
                    if dur >= min_duration:
                        scenes[len(scenes) - 1].append(self.parent.delta2QTime(start))
                        scenes.append([self.parent.delta2QTime(end)])
            last = scenes[len(scenes) - 1][0]
            dur = self.duration()
            if last < dur and (last.msecsTo(dur) / 1000) >= min_duration:
                scenes[len(scenes) - 1].append(dur)
            else:
                scenes.pop()
            if os.getenv('DEBUG', False) or getattr(self.parent, 'verboseLogs', False):
                self.logger.info(scenes)
            self.addScenes.emit(scenes)

    def killFilterProc(self) -> None:
        if hasattr(self, 'filterproc') and self.filterproc.state() != QProcess.NotRunning:
            self.filterproc.kill()

    def probe(self, source: str) -> Munch:
        try:
            args = [
                '-v', 'error',
                '-show_streams',
                '-show_format',
                '-of', 'json',
                source,
            ]
            json_data = self.cmdExec(self.backends.ffprobe, args, output=True, mergechannels=False)
            return Munch.fromDict(loads(json_data))
        except FileNotFoundError:
            self.logger.exception('FFprobe could not find media file: {}'.format(source), exc_info=True)
            raise
        except JSONDecodeError:
            self.logger.exception('FFprobe JSON decoding error', exc_info=True)
            raise

    def getKeyframes(self, source: str, formatted_time: bool = False) -> List[Union[str, float]]:
        """
        Return a list of key-frame times.

        TODO: change this to return a list of key-frame times for specific sub-streams
        Different sub-streams in a container (e.g. in MPEG2-TS) may contain keyframes at different positions. See this comment for more information:
        https://github.com/ozmartian/vidcutter/issues/257#issuecomment-569889644

        :param source: The file name of the media file.
        :param formatted_time: If `True`, return times list of strings. Defaults to `False`, which returns times as list of floats.
        :returns: a list of key-frame times, eiter formatted as strings or floats.
        """
        if len(self.keyframes) and source == self.source:
            return self.keyframes
        timecode = '0:00:00.000000' if formatted_time else 0

        # for mpeg2ts movies the pts_time is never N/A
        # Note that pts_time and dts_time are equal when both exist and pts_time is N/A for h264 content.
        args = [
            '-v', 'error',
            '-show_packets',
            '-select_streams', 'v',
            '-show_entries', 'packet=pts_time,dts_time,flags',
        ] + (['-sexagesimal'] if formatted_time else []) + [
            '-of', 'csv',
            source,
        ]
        result = self.cmdExec(self.backends.ffprobe, args, output=True, suppresslog=True, mergechannels=False)
        keyframe_times = []
        for line in result.split('\n'):
            parts = line.split(',')
            # For some streams, e.g. DVB-T recorded MPEG2TS, the output may look like below.
            # in other words, some lines may be empty. Those are the lines following packets with the side_data flag
            # ==== ffprobe output BEGIN ======
            # packet,audio,1,95942.464222,95942.464222,K_side_data,
            #
            # packet,audio,1,95942.488222,95942.488222,K_
            # packet,subtitle,2,95942.550667,95942.550667,K_side_data,
            #
            # packet,audio,3,95942.464222,95942.464222,K_side_data,
            #
            # packet,audio,3,95942.488222,95942.488222,K_
            # packet,video,0,95942.910667,95942.910667,__
            # ==== ffprobe output BEGIN ======
            #
            # It is therefore important to check for the length of the split
            if len(parts) > 1:
                if parts[1] != 'N/A':
                    timecode = parts[1]
                else:
                    timecode = parts[2]
                if re.search(',K', line):
                    if formatted_time:
                        keyframe_times.append(timecode[:-3])
                    else:
                        keyframe_times.append(float(timecode))
        #last_keyframe = self.duration().toString('h:mm:ss.zzz')
        last_keyframe = self.durationSecs()
        if keyframe_times[-1] != last_keyframe:
            keyframe_times.append(last_keyframe)
        if source == self.source and not formatted_time:
            self.keyframes = keyframe_times
        return keyframe_times

    def getGOPbisections(self, keyframes: [], start: float, end: float) -> Dict[str, Tuple[float, float, float]]:
        """
        Return a mapping of the start and end time to the 3 surronging key-frames.

        :param keyframes: the keyframes to bisect for start / end
        :param start: The start time.
        :param end: The end time.
        :returns: A dictionary mapping `start` and `end` to 3-tuples
            `start` => (seek time, start of start segment GOP, end of start segment GOP & start of middle segment);
            `end` => (seek time, end of middle segment & start of end segment GOP, end of end segment GOP).
        """

        start_pos = bisect_right(keyframes, start)
        end_pos = bisect_left(keyframes, end)
        return {
            'start': (
                keyframes[start_pos-2] if start_pos > 1 else keyframes[start_pos-1] if start_pos > 0 else keyframes[start_pos],
                keyframes[start_pos-1] if start_pos > 0 else keyframes[start_pos],
                keyframes[start_pos]
            ),
            'end': (
                keyframes[end_pos-2],
                keyframes[end_pos-1],
                keyframes[end_pos] if end_pos != len(keyframes) else keyframes[end_pos-1],
            )
        }

    def isMPEGcodec(self, source: str = None) -> bool:
        if source is None and hasattr(self.streams, 'video'):
            codec = self.streams.video.codec_name
        else:
            codec = self.codecs(source)[0].lower()
            if codec == 'mpeg4' and os.path.splitext(source)[1] == '.avi':
                return False
        return codec in VideoService.config.mpeg_formats

    # noinspection PyBroadException
    def mpegtsJoin(self, inputs: list, output: str, chapters: Optional[List[str]]=None) -> bool:
        result = False
        try:
            self.checkDiskSpace(output)
            outfiles = []
            video_bsf, audio_bsf = self.getBSF(inputs[0])
            # 1. transcode to mpeg transport streams
            for file in inputs:
                if not file:
                    continue
                name, _ = os.path.splitext(file)
                outfile = '{}-transcoded.ts'.format(name)
                outfiles.append(outfile)
                if os.path.isfile(outfile):
                    os.remove(outfile)
                args = [
                    '-v', 'error',
                    '-i', file,
                    '-c', 'copy',
                    '-map', '0',
                    video_bsf,
                    '-f', 'mpegts',
                    outfile,
                ]
                if not self.cmdExec(self.backends.ffmpeg, args):
                    return result
            # 2. losslessly concatenate at the file level
            if len(outfiles):
                if os.path.isfile(output):
                    os.remove(output)
                ffmetadata = None
                if chapters is not None and len(chapters):
                    ffmetadata = self.getChapterFile(outfiles, chapters)
                    metadata = ['-i ', ffmetadata, '-map_metadata', '1']
                else:
                    metadata = []
                args = [
                    '-v', 'error',
                    '-i', "concat:{0}".format("|".join(map(str, outfiles))),
                ] + metadata + [
                    '-c', 'copy',
                    audio_bsf,
                    output,
                ]
                result = self.cmdExec(self.backends.ffmpeg, args)
                # 3. cleanup mpegts files
                [os.remove(file) for file in outfiles]
                if chapters and ffmetadata is not None:
                    os.remove(ffmetadata)
        except BaseException:
            self.logger.exception('Exception during MPEG-TS join', exc_info=True)
            result = False
        return result

    def version(self) -> str:
        args = ['-version']
        result = self.cmdExec(self.backends.ffmpeg, args, True)
        return re.search(r'ffmpeg\sversion\s([\S]+)\s', result).group(1)

    def mediainfo(self, source: str, output: str = 'HTML') -> str:
        args = ['--output', output, source]
        return self.cmdExec(self.backends.mediainfo, args, True, True)

    def cmdExec(self, cmd: str, args: List[str]=None, output: bool=False, suppresslog: bool=False, workdir: str=None,
                mergechannels: bool=True):
        if self.proc.state() == QProcess.NotRunning:
            if cmd == self.backends.mediainfo or not mergechannels:
                self.proc.setProcessChannelMode(QProcess.SeparateChannels)
            if cmd in {self.backends.ffmpeg, self.backends.ffprobe}:
                args = ['-hide_banner'] + args
            if os.getenv('DEBUG', False) or getattr(self.parent, 'verboseLogs', False):
                self.logger.info('{0} {1}'.format(cmd, ' '.join(args) if args is not None else ''))
            self.proc.setWorkingDirectory(workdir if workdir is not None else VideoService.getAppPath())
            self.proc.start(cmd, args)
            self.proc.readyReadStandardOutput.connect(
                partial(self.cmdOut, self.proc.readAllStandardOutput().data().decode('iso-8859-1').strip()))
            self.proc.waitForFinished(-1)
            if cmd == self.backends.mediainfo or not mergechannels:
                self.proc.setProcessChannelMode(QProcess.MergedChannels)
            if output:
                cmdoutput = self.proc.readAllStandardOutput().data().decode('iso-8859-1').strip()
                if getattr(self.parent, 'verboseLogs', False) and not suppresslog:
                    self.logger.info('cmd output: {}'.format(cmdoutput))
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
            QMessageBox.critical(self.parent, 'Error alert',
                                 '<h4>{0} Error:</h4><p>{1}</p>'.format(self.backends.ffmpeg, self.proc.errorString()),
                                 buttons=QMessageBox.Close)

    # noinspection PyUnresolvedReferences, PyProtectedMember
    @staticmethod
    def getAppPath(path: str = None) -> str:
        if VideoService.frozen and getattr(sys, '_MEIPASS', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        return app_path if path is None else os.path.join(app_path, path)
