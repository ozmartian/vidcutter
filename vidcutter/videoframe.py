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
            self.setWindowState(self.windowState() & ~Qt.WindowFullScreen)
            # self.setWindowFlags(Qt.Widget)
            # self.showNormal()
        else:
            self.parent.mediaPlayer.fullscreen = True
            self.setWindowState(self.windowState() | Qt.WindowFullScreen)
            self.setWindowFlags(Qt.Window)
            self.showFullScreen()
            self.parent.parent.hide()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.toggleFullscreen()
        event.accept()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if self.parent.mediaAvailable and event.type() == QEvent.WinIdChange:
            QMessageBox.warning(self, 'winId CHANGE', 'winId change has been detected.\n\n' +
                                'winId: %s\neffective winId: %s' % (self.winId().asstring(),
                                                                    self.effectiveWinId().asstring()))
        return super(VideoFrame, self).eventFilter(obj, event)

