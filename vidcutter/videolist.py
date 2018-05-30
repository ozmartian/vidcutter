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

import os
import sys

from PyQt5.QtCore import pyqtSlot, Qt, QEvent, QModelIndex, QRect, QSize, QTime
from PyQt5.QtGui import QColor, QFont, QIcon, QMouseEvent, QPainter, QPalette, QPen, QResizeEvent
from PyQt5.QtWidgets import (QAbstractItemView, QListWidget, QListWidgetItem, QProgressBar, QSizePolicy, QStyle,
                             QStyledItemDelegate, QStyleFactory, QStyleOptionViewItem)

from vidcutter.libs.graphicseffects import OpacityEffect


class VideoList(QListWidget):
    def __init__(self, parent=None):
        super(VideoList, self).__init__(parent)
        self.parent = parent
        self.theme = self.parent.theme
        self._progressbars = []
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
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setObjectName('cliplist')
        self.setStyleSheet('QListView::item { border: none; }')
        self.opacityEffect = OpacityEffect(0.3)
        self.opacityEffect.setEnabled(False)
        self.setGraphicsEffect(self.opacityEffect)

    def renderClips(self, cliptimes: list) -> int:
        self.clear()
        externalCount = 0
        for index, clip in enumerate(cliptimes):
            chapterName, endItem = '', ''
            if isinstance(clip[1], QTime):
                endItem = clip[1].toString(self.parent.timeformat)
                self.parent.totalRuntime += clip[0].msecsTo(clip[1])
            listitem = QListWidgetItem(self)
            listitem.setToolTip('Drag to reorder clips')
            if len(clip[3]):
                listitem.setToolTip(clip[3])
                externalCount += 1
            if self.parent.createChapters:
                chapterName = clip[4] if clip[4] is not None else 'Chapter {}'.format(index + 1)
            listitem.setStatusTip('Reorder clips with mouse drag & drop or right-click menu on the clip to be moved')
            listitem.setTextAlignment(Qt.AlignVCenter)
            listitem.setData(Qt.DecorationRole + 1, clip[2])
            listitem.setData(Qt.DisplayRole + 1, clip[0].toString(self.parent.timeformat))
            listitem.setData(Qt.UserRole + 1, endItem)
            listitem.setData(Qt.UserRole + 2, clip[3])
            listitem.setData(Qt.UserRole + 3, chapterName)
            listitem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled)
            self.addItem(listitem)
            if isinstance(clip[1], QTime) and not len(clip[3]):
                self.parent.seekSlider.addRegion(clip[0].msecsSinceStartOfDay(), clip[1].msecsSinceStartOfDay())
        return externalCount

    def showProgress(self, steps: int) -> None:
        for row in range(self.count()):
            item = self.item(row)
            progress = ListProgress(steps, self.visualItemRect(item), self)
            self._progressbars.append(progress)

    @pyqtSlot()
    @pyqtSlot(int)
    def updateProgress(self, item: int=None) -> None:
        if self.count():
            if item is None:
                [progress.setValue(progress.value() + 1) for progress in self._progressbars]
            else:
                self._progressbars[item].setValue(self._progressbars[item].value() + 1)

    @pyqtSlot()
    def clearProgress(self) -> None:
        for progress in self._progressbars:
            progress.hide()
            progress.deleteLater()
        self._progressbars.clear()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.count() > 0:
            if self.indexAt(event.pos()).isValid():
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        super(VideoList, self).mouseMoveEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.EnabledChange:
            self.opacityEffect.setEnabled(not self.isEnabled())

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.setFixedWidth(210 if self.verticalScrollBar().isVisible() else 190)
        self.parent.listheader.setFixedWidth(self.width())

    def clearSelection(self) -> None:
        self.parent.seekSlider.selectRegion(-1)
        self.parent.removeItemAction.setEnabled(False)
        super(VideoList, self).clearSelection()


class VideoItem(QStyledItemDelegate):
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
        thumbicon = QIcon(index.data(Qt.DecorationRole + 1))
        starttime = index.data(Qt.DisplayRole + 1)
        endtime = index.data(Qt.UserRole + 1)
        externalPath = index.data(Qt.UserRole + 2)
        chapterName = index.data(Qt.UserRole + 3)
        painter.setPen(QPen(pencolor, 1, Qt.SolidLine))
        if len(chapterName):
            offset = 20
            r = option.rect.adjusted(5, 5, 0, 0)
            cfont = QFont('Futura LT', -1, QFont.Medium)
            cfont.setPointSizeF(12.25 if sys.platform == 'darwin' else 10.25)
            painter.setFont(cfont)
            painter.drawText(r, Qt.AlignLeft, self.clipText(chapterName, painter, True))
            r = option.rect.adjusted(5, offset, 0, 0)
        else:
            offset = 0
            r = option.rect.adjusted(5, 0, 0, 0)
        thumbicon.paint(painter, r, Qt.AlignVCenter | Qt.AlignLeft)
        r = option.rect.adjusted(110, 10 + offset, 0, 0)
        painter.setFont(QFont('Noto Sans', 11 if sys.platform == 'darwin' else 9, QFont.Bold))
        painter.drawText(r, Qt.AlignLeft, 'FILENAME' if len(externalPath) else 'START')
        r = option.rect.adjusted(110, 23 + offset, 0, 0)
        painter.setFont(QFont('Noto Sans', 11 if sys.platform == 'darwin' else 9, QFont.Normal))
        if len(externalPath):
            painter.drawText(r, Qt.AlignLeft, self.clipText(os.path.basename(externalPath), painter))
        else:
            painter.drawText(r, Qt.AlignLeft, starttime)
        if len(endtime) > 0:
            r = option.rect.adjusted(110, 48 + offset, 0, 0)
            painter.setFont(QFont('Noto Sans', 11 if sys.platform == 'darwin' else 9, QFont.Bold))
            painter.drawText(r, Qt.AlignLeft, 'RUNTIME' if len(externalPath) else 'END')
            r = option.rect.adjusted(110, 60 + offset, 0, 0)
            painter.setFont(QFont('Noto Sans', 11 if sys.platform == 'darwin' else 9, QFont.Normal))
            painter.drawText(r, Qt.AlignLeft, endtime)

    def clipText(self, text: str, painter: QPainter, chapter: bool=False) -> str:
        metrics = painter.fontMetrics()
        return metrics.elidedText(text, Qt.ElideRight, (self.parent.width() - 10 if chapter else 100 - 10))

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(185, 105 if self.parent.parent.createChapters else 85)


class ListProgress(QProgressBar):
    def __init__(self, steps: int, geometry: QRect, parent=None):
        super(ListProgress, self).__init__(parent)
        self.setStyle(QStyleFactory.create('Fusion'))
        self.setRange(0, steps)
        self.setValue(0)
        self.setGeometry(geometry)
        palette = self.palette()
        palette.setColor(QPalette.Highlight, QColor(100, 44, 104))
        self.setPalette(palette)
        self.show()
