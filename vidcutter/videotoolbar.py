#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtWidgets import QToolBar, QToolButton


class VideoToolBar(QToolBar):
    def __init__(self, *arg, **kwargs):
        super(VideoToolBar, self).__init__(*arg, **kwargs)

    def disableTooltips(self):
        for button in self.findChildren(QToolButton):
            button.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            return True
        elif event.type() == QEvent.StatusTip and not obj.isEnabled():
            return True
        return QToolBar.eventFilter(self, obj, event)
