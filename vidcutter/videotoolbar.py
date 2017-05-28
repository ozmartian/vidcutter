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

from PyQt5.QtCore import pyqtSlot, QEvent, QObject, Qt
from PyQt5.QtWidgets import QAction, qApp, QStyleFactory, QToolBar, QToolButton


class VideoToolBar(QToolBar):
    def __init__(self, parent=None, *arg, **kwargs):
        super(VideoToolBar, self).__init__(parent, *arg, **kwargs)
        self.parent = parent
        self.setObjectName('appcontrols')
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        if sys.platform == 'darwin':
            self.setStyle(QStyleFactory.create('Fusion'))

    def disableTooltips(self) -> None:
        buttonlist = self.findChildren(QToolButton)
        for button in buttonlist:
            button.installEventFilter(self)
            if button == buttonlist[len(buttonlist)-1]:
                button.setObjectName('saveButton')

    @pyqtSlot(QAction)
    def setLabels(self, action: QAction) -> None:
        if action == self.parent.besideLabelsAction:
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            for button in self.findChildren(QToolButton):
                button.setText(button.text().replace(' ', '\n'))
        elif action == self.parent.underLabelsAction:
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            for button in self.findChildren(QToolButton):
                button.setText(button.text().replace('\n', ' '))
        elif action == self.parent.noLabelsAction:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)

    def setLabelByType(self, label_type: str) -> None:
        if label_type == 'beside':
            self.parent.besideLabelsAction.setChecked(True)
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            for button in self.findChildren(QToolButton):
                button.setText(button.text().replace(' ', '\n'))
        elif label_type == 'under':
            self.parent.underLabelsAction.setChecked(True)
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            for button in self.findChildren(QToolButton):
                button.setText(button.text().replace('\n', ' '))
        elif label_type == 'none':
            self.parent.noLabelsAction.setChecked(True)
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)

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
