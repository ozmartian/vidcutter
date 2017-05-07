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

from locale import setlocale, LC_NUMERIC

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

try:
    import vidcutter.libs.mpv as mpv
    mpv_error = False
except OSError:
    mpv_error = True


class LibMPV(QObject):
    def __init__(self, parent=None, ):
        super(LibMPV, self).__init__(parent)
        setlocale(LC_NUMERIC, 'C')
        self.player = mpv.MPV()

    # TODO

    # def initMPV(self):
    #     setlocale(LC_NUMERIC, 'C')
    #     self.mpvFrame = VideoFrame(self)
    #     if self.mediaPlayer is not None:
    #         self.mediaPlayer.terminate()
    #         del self.mediaPlayer
    #
    #     self.mediaPlayer = mpv.MPV(wid=int(self.mpvFrame.winId()),
    #                                log_handler=self.logMPV,
    #                                ytdl=False,
    #                                pause=True,
    #                                keep_open=True,
    #                                idle=True,
    #                                osc=False,
    #                                cursor_autohide=False,
    #                                input_cursor=False,
    #                                input_default_bindings=False,
    #                                stop_playback_on_init_failure=False,
    #                                input_vo_keyboard=False,
    #                                sub_auto=False,
    #                                osd_level=0,
    #                                sid=False,
    #                                # cache_backbuffer=(10 * 1024),
    #                                # cache_default=(10 * 1024),
    #                                # demuxer_max_bytes=(25 * 1024 * 1024),
    #                                hr_seek='absolute',
    #                                hr_seek_framedrop=True,
    #                                # rebase_start_time=False,
    #                                keepaspect=self.keepRatioAction.isChecked(),
    #                                hwdec='auto' if self.hardwareDecodingAction.isChecked() else 'no')
    #
    #     self.mediaPlayer.observe_property('time-pos', lambda ptime: self.positionChanged(ptime))
    #     self.mediaPlayer.observe_property('duration', lambda dtime: self.durationChanged(dtime))

    def __del__(self):
        self.player.terminate()
