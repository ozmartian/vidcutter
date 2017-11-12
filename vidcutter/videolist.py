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

import os
import sys

from PyQt5.QtCore import Qt, QEvent, QModelIndex, QSize
from PyQt5.QtGui import QColor, QFont, QIcon, QMouseEvent, QPainter, QPen
from PyQt5.QtWidgets import (QAbstractItemDelegate, QAbstractItemView, QListWidget, QSizePolicy, QStyle,
                             QStyleOptionViewItem)

from vidcutter.graphicseffects import OpacityEffect


class VideoList(QListWidget):
    def __init__(self, parent=None):
        super(VideoList, self).__init__(parent)
        self.parent = parent
        self.theme = self.parent.theme
        self.setMouseTracking(True)
        self.setDropIndicatorShown(True)
        self.setFixedWidth(190)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setContentsMargins(0, 0, 0, 0)
        self.setItemDelegate(VideoItem(self))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setUniformItemSizes(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAlternatingRowColors(True)
        self.setObjectName('cliplist')
        self.setStyleSheet('QListView::item { border: none; }')
        self.opacityEffect = OpacityEffect(0.3)
        self.opacityEffect.setEnabled(False)
        self.setGraphicsEffect(self.opacityEffect)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.count() > 0:
            modelindex = self.indexAt(event.pos())
            if modelindex.isValid():
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        super(VideoList, self).mouseMoveEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.EnabledChange:
            self.opacityEffect.setEnabled(not self.isEnabled())

    def clearSelection(self) -> None:
        self.parent.seekSlider.selectRegion(-1)
        self.parent.removeItemAction.setEnabled(False)
        super(VideoList, self).clearSelection()


class VideoItem(QAbstractItemDelegate):
    def __init__(self, parent: VideoList=None):
        super(VideoItem, self).__init__(parent)
        self.parent = parent
        self.theme = self.parent.theme

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        r = option.rect
        pencolor = Qt.white if self.theme == 'dark' else Qt.black
        if self.parent.isEnabled():
            if option.state & QStyle.State_Selected:
                painter.setBrush(QColor(150, 190, 78, 150))
            elif option.state & QStyle.State_MouseOver:
                painter.setBrush(QColor(227, 212, 232))
                pencolor = Qt.black
            else:
                brushcolor = QColor(79, 85, 87, 175) if self.theme == 'dark' else QColor('#EFF0F1')
                painter.setBrush(Qt.transparent if index.row() % 2 == 0 else brushcolor)
        painter.setPen(Qt.NoPen)
        painter.drawRect(r)
        thumb = QIcon(index.data(Qt.DecorationRole + 1))
        starttime = index.data(Qt.DisplayRole + 1)
        endtime = index.data(Qt.UserRole + 1)
        externalPath = index.data(Qt.UserRole + 2)
        r = option.rect.adjusted(5, 0, 0, 0)
        thumb.paint(painter, r, Qt.AlignVCenter | Qt.AlignLeft)
        painter.setPen(QPen(pencolor, 1, Qt.SolidLine))
        r = option.rect.adjusted(110, 8, 0, 0)
        painter.setFont(QFont('Noto Sans UI', 10 if sys.platform == 'darwin' else 8, QFont.Bold))
        painter.drawText(r, Qt.AlignLeft, 'FILENAME' if len(externalPath) else 'START')
        r = option.rect.adjusted(110, 20, 0, 0)
        painter.setFont(QFont('Noto Sans UI', 11 if sys.platform == 'darwin' else 9, QFont.Normal))
        if len(externalPath):
            painter.drawText(r, Qt.AlignLeft, self.clipText(os.path.basename(externalPath), painter))
        else:
            painter.drawText(r, Qt.AlignLeft, starttime)
        if len(endtime) > 0:
            r = option.rect.adjusted(110, 45, 0, 0)
            painter.setFont(QFont('Noto Sans UI', 10 if sys.platform == 'darwin' else 8, QFont.Bold))
            painter.drawText(r, Qt.AlignLeft, 'RUNTIME' if len(externalPath) else 'END')
            r = option.rect.adjusted(110, 60, 0, 0)
            painter.setFont(QFont('Noto Sans UI', 11 if sys.platform == 'darwin' else 9, QFont.Normal))
            painter.drawText(r, Qt.AlignLeft, endtime)
        if self.parent.verticalScrollBar().isVisible():
            self.parent.setFixedWidth(210)
        else:
            self.parent.setFixedWidth(190)

    def clipText(self, text: str, painter: QPainter) -> str:
        metrics = painter.fontMetrics()
        return metrics.elidedText(text, Qt.ElideRight, (self.parent.width() - 100 - 10))

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(185, 85)
