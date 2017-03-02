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

from PyQt5.QtCore import QModelIndex, Qt, QSize
from PyQt5.QtGui import QPainter, QColor, QIcon, QPen, QFont, QMouseEvent
from PyQt5.QtWidgets import QAbstractItemDelegate, QStyleOptionViewItem, QStyle, QListWidget


class VideoList(QListWidget):
    def __init__(self, *arg, **kwargs):
        super(VideoList, self).__init__(*arg, **kwargs)
        self.itemPressed.connect(lambda item: self.parentWidget().seekSlider.highlightRegion(self.row(item)))
        self.setMouseTracking(True)
        self.setDropIndicatorShown(True)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.count() > 0:
            modelindex = self.indexAt(event.pos())
            if modelindex.isValid():
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        super(VideoList, self).mouseMoveEvent(event)


class VideoItem(QAbstractItemDelegate):
    def __init__(self, parent=None):
        super(VideoItem, self).__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        r = option.rect
        if option.state & QStyle.State_Selected:
            painter.setBrush(QColor('#96BE4E'))
        elif option.state & QStyle.State_MouseOver:
            painter.setBrush(QColor('#E3D4E8'))
        else:
            painter.setBrush(Qt.transparent if index.row() % 2 == 0 else QColor('#EFF0F1'))
        painter.setPen(Qt.NoPen)
        painter.drawRect(r)
        thumb = QIcon(index.data(Qt.DecorationRole))
        starttime = index.data(Qt.DisplayRole)
        endtime = index.data(Qt.UserRole + 1)
        r = option.rect.adjusted(5, 0, 0, 0)
        thumb.paint(painter, r, Qt.AlignVCenter | Qt.AlignLeft)
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        r = option.rect.adjusted(110, 8, 0, 0)
        painter.setFont(QFont('Open Sans', 8, QFont.Bold))
        painter.drawText(r, Qt.AlignLeft, 'START')
        r = option.rect.adjusted(110, 20, 0, 0)
        painter.setFont(QFont('Open Sans', 9, QFont.Normal))
        painter.drawText(r, Qt.AlignLeft, starttime)
        if len(endtime) > 0:
            r = option.rect.adjusted(110, 45, 0, 0)
            painter.setFont(QFont('Open Sans', 8, QFont.Bold))
            painter.drawText(r, Qt.AlignLeft, 'END')
            r = option.rect.adjusted(110, 60, 0, 0)
            painter.setFont(QFont('Open Sans', 9, QFont.Normal))
            painter.drawText(r, Qt.AlignLeft, endtime)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(185, 85)
