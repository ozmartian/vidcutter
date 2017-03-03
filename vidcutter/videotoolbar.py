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

from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtWidgets import QToolBar, QToolButton


class VideoToolBar(QToolBar):
    def __init__(self, *arg, **kwargs):
        super(VideoToolBar, self).__init__(*arg, **kwargs)

    def disableTooltips(self):
        c = 1
        total = len(self.findChildren(QToolButton))
        for button in self.findChildren(QToolButton):
            button.installEventFilter(self)
            if c == total:
                button.setObjectName('saveButton')
            c += 1

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            return True
        elif event.type() == QEvent.StatusTip and not obj.isEnabled():
            return True
        return super(VideoToolBar, self).eventFilter(obj, event)
