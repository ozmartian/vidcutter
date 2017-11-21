#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

from enum import Enum

from PyQt5.QtWidgets import QDialog


class StreamType(Enum):
    VIDEO = 0,
    AUDIO = 1,
    TEXT = 2


class StreamEditor(QDialog):

    def __init__(self, parent=None):
        super(StreamEditor, self).__init__(parent)
