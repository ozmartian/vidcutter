#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
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
#######################################################################

import sys

from PyQt5.QtCore import pyqtSlot, QEvent, QObject, QSize, Qt
from PyQt5.QtWidgets import qApp, QStyleFactory, QToolBar, QToolButton


class VideoToolBar(QToolBar):
    def __init__(self, parent=None):
        super(VideoToolBar, self).__init__(parent)
        self.parent = parent
        self.setObjectName('appcontrols')
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setFloatable(False)
        self.setMovable(False)
        self.setIconSize(QSize(50, 53))
        if sys.platform == 'darwin':
            self.setStyle(QStyleFactory.create('Fusion'))

    def disableTooltips(self) -> None:
        buttonlist = self.findChildren(QToolButton)
        for button in buttonlist:
            button.installEventFilter(self)
            if button == buttonlist[len(buttonlist)-1]:
                button.setObjectName('saveButton')

    @pyqtSlot(int)
    def setLabels(self, option_id: int) -> None:
        if option_id == 3:
            self.setLabelByType('beside')
        elif option_id == 2:
            self.setLabelByType('under')
        elif option_id == 1:
            self.setLabelByType('none')

    def setLabelByType(self, label_type: str) -> None:
        if label_type == 'beside':
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            [button.setText(button.text().replace(' ', '\n')) for button in self.findChildren(QToolButton)]
        elif label_type == 'under':
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            [button.setText(button.text().replace('\n', ' ')) for button in self.findChildren(QToolButton)]
        elif label_type == 'none':
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.parent.settings.setValue('toolbarLabels', label_type)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            return True
        elif event.type() == QEvent.Enter and obj.isEnabled():
            qApp.setOverrideCursor(Qt.PointingHandCursor)
        elif event.type() == QEvent.Leave:
            qApp.restoreOverrideCursor()
        elif event.type() == QEvent.StatusTip and not obj.isEnabled():
            return True
        return super(VideoToolBar, self).eventFilter(obj, event)
