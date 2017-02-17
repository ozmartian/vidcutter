#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
                button.setStyleSheet('QToolButton { color:#642C68; } QToolButton:disabled { color:#999; }')
            c += 1

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            return True
        elif event.type() == QEvent.StatusTip and not obj.isEnabled():
            return True
        return super(VideoToolBar, self).eventFilter(obj, event)
