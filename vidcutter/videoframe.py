#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QFrame, QMessageBox


class VideoFrame(QFrame):
    def __init__(self, parent=None, *arg, **kwargs):
        super(VideoFrame, self).__init__(parent, *arg, **kwargs)
        self.parent = parent
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WA_NativeWindow)
        self.installEventFilter(self)

    def toggleFullscreen(self) -> None:
        if self.isFullScreen():
            self.parent.mediaPlayer.fullscreen = False
            self.parent.mediaPlayer.wid = self.parent.parent.winId()
            self.setWindowState(self.windowState() & ~Qt.WindowFullScreen)
            self.setWindowFlags(Qt.Widget)
            self.parent.parent.show()
            self.showNormal()
        else:
            self.parent.mediaPlayer.fullscreen = True
            self.parent.parent.hide()
            self.parent.id = None
            self.setWindowState(self.windowState() | Qt.WindowFullScreen)
            self.setWindowFlags(Qt.Window)
            self.showFullScreen()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.toggleFullscreen()
        event.accept()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if self.parent.mediaAvailable and event.type() == QEvent.WinIdChange:
            self.parent.mediaPlayer.wid = self.winId()
        return super(VideoFrame, self).eventFilter(obj, event)

