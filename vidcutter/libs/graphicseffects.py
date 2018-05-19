#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
#
# copyright © 2018 Pete Alexandrou
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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QTransform
from PyQt5.QtWidgets import QGraphicsEffect


class OpacityEffect(QGraphicsEffect):
    def __init__(self, opacity: float=0.6):
        super(OpacityEffect, self).__init__()
        self.opacity = opacity

    def draw(self, painter: QPainter) -> None:
        if self.sourceIsPixmap():
            pixmap, offset = self.sourcePixmap(Qt.LogicalCoordinates, QGraphicsEffect.PadToEffectiveBoundingRect)
        else:
            pixmap, offset = self.sourcePixmap(Qt.DeviceCoordinates, QGraphicsEffect.PadToEffectiveBoundingRect)
            painter.setWorldTransform(QTransform())
        painter.setBrush(Qt.black)
        painter.drawRect(pixmap.rect())
        painter.setOpacity(self.opacity)
        painter.drawPixmap(offset, pixmap)
