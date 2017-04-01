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

import sys

from PyQt5.QtCore import pyqtSlot, QObject, QEvent, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QStyleFactory, QToolBar, QToolButton


class VideoToolBar(QToolBar):
    def __init__(self, parent=None, *arg, **kwargs):
        super(VideoToolBar, self).__init__(parent, *arg, **kwargs)
        self.parent = parent
        self.settings = self.parent.settings
        self.setObjectName('appcontrols')
        self.setLabelPosition(checked=bool(self.settings.value('labelPosition', True)), save=False)
        self.toggleLabels(checked=bool(self.settings.value('showLabels', True)), save=False)
        if sys.platform == 'darwin':
            self.setStyle(QStyleFactory.create('Fusion'))

    def disableTooltips(self):
        buttonlist = self.findChildren(QToolButton)
        for button in buttonlist:
            button.installEventFilter(self)
            if button == buttonlist[len(buttonlist)-1]:
                button.setObjectName('saveButton')

    @pyqtSlot(bool)
    def setCompactMode(self, checked: bool = False):
        pass

    @pyqtSlot(bool)
    def setLabelPosition(self, checked: bool = True, save: bool = True):
        if checked:
            self.labelPosition = Qt.ToolButtonTextBesideIcon
            for button in self.findChildren(QToolButton):
                button.setText(button.text().replace(' ', '\n'))
        else:
            self.labelPosition = Qt.ToolButtonTextUnderIcon
            for button in self.findChildren(QToolButton):
                button.setText(button.text().replace('\n', ' '))
        self.setToolButtonStyle(self.labelPosition)
        if save:
            self.settings.setValue('labelPosition', checked)

    @pyqtSlot(bool)
    def toggleLabels(self, checked: bool = True, save: bool = True):
        if not checked:
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        else:
            self.setToolButtonStyle(self.labelPosition)
        if save:
            self.settings.setValue('showLabels', checked)

    def mouseMoveEvent(self, event: QMouseEvent):
        pass

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            return True
        elif event.type() == QEvent.StatusTip and not obj.isEnabled():
            return True
        return super(VideoToolBar, self).eventFilter(obj, event)
