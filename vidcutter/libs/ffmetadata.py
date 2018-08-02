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

from typing import List


class FFMetadataChapter:
    def __init__(self):
        super(FFMetadataChapter, self).__init__()
        self._timebase = '1/1000'
        self._start_time = 0
        self._end_time = 0

    @property
    def timebase(self) -> str:
        return self._timebase

    @timebase.setter
    def timebase(self, value: str) -> None:
        self._timebase = value

    @property
    def start_time(self) -> int:
        return self._start_time

    @start_time.setter
    def start_time(self, value: int) -> None:
        self._start_time = value

    @property
    def end_time(self) -> int:
        return self._end_time

    @end_time.setter
    def end_time(self, value: int) -> None:
        self._end_time = value

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value


class FFMetadata:
    _file_header = ';FFMETADATA1'
    _section_name = 'CHAPTER'

    def __init__(self):
        super(FFMetadata, self).__init__()
        self._chapters = []

    @property
    def file_header(self) -> str:
        return self._file_header

    @property
    def section_name(self) -> str:
        return self._section_name

    @property
    def chapters(self) -> List[FFMetadataChapter]:
        return self._chapters

    @property
    def count(self) -> int:
        return len(self._chapters)

    def add_chapter(self, start: int, end: int, title: str=None, timebase: str=None) -> None:
        chapter = FFMetadataChapter()
        chapter.start_time = start
        chapter.end_time = end
        chapter.title = title if title is not None else 'Chapter {}'.format(self.count + 1)
        if timebase is not None:
            chapter.timebase = timebase
        self._chapters.append(chapter)

    def output(self) -> str:
        data = '{}\n\n'.format(self.file_header)
        for chapter in self._chapters:
            data += '[{0}]\nTIMEBASE={1}\nSTART={2}\nEND={3}\ntitle={4}\n' \
                    .format(self.section_name, chapter.timebase, chapter.start_time, chapter.end_time, chapter.title)
        return data
