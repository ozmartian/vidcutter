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

from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QFrame


class VideoFrame(QFrame):
    def __init__(self, parent=None, *arg, **kwargs):
        super(VideoFrame, self).__init__(parent, *arg, **kwargs)
        self.parent = parent
        self.setEnabled(False)
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WA_NativeWindow)
        self.setCursor(Qt.ArrowCursor)
        self.installEventFilter(self)

    # def toggleFullscreen(self) -> None:
    #     if self.isFullScreen():
    #         self.parent.mediaPlayer.fullscreen = False
    #         self.parent.mediaPlayer.wid = self.parent.parent.winId()
    #         self.setWindowState(self.windowState() & ~Qt.WindowFullScreen)
    #         self.setWindowFlags(Qt.Widget)
    #         self.parent.parent.show()
    #         self.showNormal()
    #     else:
    #         self.parent.mediaPlayer.fullscreen = True
    #         self.parent.parent.hide()
    #         self.parent.id = None
    #         self.setWindowState(self.windowState() | Qt.WindowFullScreen)
    #         self.setWindowFlags(Qt.Window)
    #         self.showFullScreen()
    #
    # def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
    #     # self.toggleFullscreen()
    #     event.accept()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if self.parent.mediaAvailable and event.type() == QEvent.WinIdChange:
            self.parent.mediaPlayer.wid = self.winId()
        return super(VideoFrame, self).eventFilter(obj, event)
