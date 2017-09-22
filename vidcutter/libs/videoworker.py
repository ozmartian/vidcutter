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
import shlex
import sys
import traceback

from PyQt5.QtCore import pyqtSignal, QObject, QProcess, QRunnable


class VideoSignals(QObject):
    error = pyqtSignal(tuple)
    result = pyqtSignal(list)
    progress = pyqtSignal(str)


class VideoWorker(QRunnable):
    def __init__(self, cmd: str, args: str, progresstxt: str, uselog: bool=False):
        super(VideoWorker, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.cmd = cmd
        self.args = args
        self.progresstxt = progresstxt
        self.uselog = uselog
        self.signals = VideoSignals()

    def run(self):
        results = []
        # noinspection PyBroadException
        try:
            self.proc = QProcess()
            self.proc.setProcessChannelMode(QProcess.MergedChannels)
            if self.proc.state() == QProcess.NotRunning:
                if self.uselog:
                    self.logger.info('{0} {1}'.format(self.cmd, self.args))
                self.signals.progress.emit(self.progresstxt)
                self.proc.start(self.cmd, shlex.split('-hide_banner {}'.format(self.args)))
                self.proc.waitForFinished(-1)
                results.append(self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0)
        except BaseException:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(results)
