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

from enum import Enum

from PyQt5.QtCore import QSize

from vidcutter.libs.munch import Munch


class Config:
    @staticmethod
    def filter_settings() -> Munch:
        return Munch(
            blackdetect=Munch(
                min_duration=0.1,
                default_duration=2.0
            )
        )

    @property
    def thumbnails(self) -> dict:
        return {'INDEX': QSize(100, 70), 'TIMELINE': QSize(105, 60)}

    @property
    def video_codecs(self) -> list:
        return ['flv', 'h263', 'libvpx', 'libx264', 'libx265', 'libxvid', 'mpeg2video', 'mpeg4', 'msmpeg4', 'wmv2']

    @property
    def audio_codecs(self) -> list:
        return ['aac', 'ac3', 'libfaac', 'libmp3lame', 'libvo_aacenc', 'libvorbis', 'mp2', 'wmav2']

    @property
    def formats(self) -> list:
        return [
            '3g2', '3gp', 'aac', 'ac3', 'avi', 'dv', 'flac', 'flv', 'm4a', 'm4v', 'mka', 'mkv', 'mov', 'mp3',
            'mp4', 'mpg', 'ogg', 'vob', 'wav', 'webm', 'wma', 'wmv'
        ]

    @property
    def mpeg_formats(self) -> list:
        return [
            'h264', 'hevc', 'mpeg4', 'divx', 'xvid', 'webm', 'ivf', 'vp9', 'mpeg2video', 'mpg2', 'mp2', 'mp3',
            'aac'
        ]

    @property
    def encoding(self) -> dict:
        return {
            'hevc': 'libx265 -tune zerolatency -preset ultrafast -x265-params crf=23 -qp 4 -flags +cgop',
            'h264': 'libx264 -tune film -preset ultrafast -x264-params crf=23 -qp 0 -flags +cgop',
            'vp9': 'libvpx-vp9 -deadline best -quality best'
        }

    @property
    def binaries(self) -> dict:
        return {
            'nt': {  # Windows
                'ffmpeg': ['ffmpeg.exe'],
                'ffprobe': ['ffprobe.exe'],
                'mediainfo': ['MediaInfo.exe']
            },
            'posix': {  # Linux + macOS
                'ffmpeg': ['ffmpeg', 'avconv'],
                'ffprobe': ['ffprobe', 'avprobe'],
                'mediainfo': ['mediainfo']
            }
        }

    @property
    def filters(self) -> dict:
        return {
            'all': [
                '3g2', '3gp', 'amv', 'asf', 'asx', 'avi', 'bin', 'dat', 'div', 'divx', 'f4v', 'flv',
                'm1v', 'm2t', 'm2ts', 'm2v', 'm4v', 'mjpeg', 'mjpg', 'mkv', 'mod', 'mov', 'mp1', 'mp3',
                'mp4', 'mpa', 'mpe', 'mpeg', 'mpg', 'mpv', 'mpv4', 'qt', 'rm', 'rmvb', 'tod', 'ts',
                'vob', 'wav', 'webm', 'wma', 'wmv', 'wtv', 'xvid'
            ],
            'types': [
                '3GPP files (*.3gp *.3g2)', 'AMV files (*.amv)', 'AVI files (*.avi)', 'DivX files (*.divx *.div)',
                'Flash files (*.flv *.f4v)', 'WebM files (*.webm)', 'MKV files (*.mkv)',
                'MPEG Audio files (*.mp3 *.mpa *.mp1)', 'MPEG files (*.mpeg *.mpg *.mpe *.m1v *.tod)',
                'MPEG-2 files (*.mpv *.m2v *.ts *.m2t *.m2ts)', 'MPEG-4 files (*.mp4 *.m4v *.mpv4)',
                'MOD files (*.mod)', 'MJPEG files (*.mjpg *.mjpeg)', 'QuickTime files (*.mov *.qt)',
                'RealMedia files (*.rm *.rmvb)', 'VCD DAT files (*.dat)', 'VCD SVCD BIN/CUE images (*.bin)',
                'VOB files (*.vob)', 'Wave Audio files (*.wav)', 'Windows Media audio (*.wma)',
                'Windows Media files (*.asf *.asx *.wmv)', 'Windows Recorded TV files (*.wtv)', 'Xvid files (*.xvid)'
            ]
        }


class Streams(Enum):
    VIDEO = 0
    AUDIO = 1
    SUBTITLE = 2


class VideoFilter(Enum):
    BLACKDETECT = 1


class VidCutterException(Exception):
    def __init__(self, msg: str=None):
        super(VidCutterException, self).__init__(msg)
        self.msg = msg


class InvalidMediaException(VidCutterException):
    def __init__(self, msg: str=None):
        super(InvalidMediaException, self).__init__(msg)


class ToolNotFoundException(VidCutterException):
    def __init__(self, msg: str=None):
        super(ToolNotFoundException, self).__init__(msg)


class cached_property(object):
    def __init__(self, f):
        self._funcname = f.__name__
        self._f = f

    def __get__(self, obj, owner):
        ret = obj.__dict__[self._funcname] = self._f(obj)
        return ret
