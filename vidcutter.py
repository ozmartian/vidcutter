#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import re
import signal
import sys
import time
import warnings
from zipfile import ZipFile

from PyQt5.QtCore import QDir, QFile, QFileInfo, QModelIndex, QPoint, QSize, Qt, QTime, QUrl, pyqtSlot
from PyQt5.QtGui import (QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent, QFont, QFontDatabase, QIcon,
                         QKeyEvent, QMouseEvent, QMovie, QPalette, QPixmap, QWheelEvent)
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QApplication, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QProgressDialog,
                             QPushButton, QSizePolicy, QStyleFactory, QSlider, QToolBar, QVBoxLayout, QWidget,
                             qApp)
from qtawesome import icon

try:
    from vidcutter.updater import Updater
    from vidcutter.videoservice import VideoService
    from vidcutter.videoslider import VideoSlider
    import vidcutter.resources as resources
except ImportError:
    from updater import Updater
    from videoservice import VideoService
    from videoslider import VideoSlider
    import resources

signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)
warnings.filterwarnings('ignore')


class VideoWidget(QVideoWidget):
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        p = self.palette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)
        self.setAttribute(Qt.WA_OpaquePaintEvent)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.setFullScreen(False)
            event.accept()
        elif event.key() == Qt.Key_Enter:
            self.setFullScreen(not self.isFullScreen())
            event.accept()
        else:
            super(VideoWidget, self).keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.setFullScreen(not self.isFullScreen())
        event.accept()


class VidCutter(QWidget):
    def __init__(self, parent):
        super(VidCutter, self).__init__(parent)
        self.novideoWidget = QWidget(self, autoFillBackground=True)
        self.parent = parent
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videoWidget = VideoWidget(self)
        self.videoService = VideoService(self)

        QFontDatabase.addApplicationFont(MainWindow.get_path('fonts/DroidSansMono.ttf'))
        QFontDatabase.addApplicationFont(MainWindow.get_path('fonts/OpenSans.ttf'))

        fontSize = 12 if sys.platform == 'darwin' else 10
        appFont = QFont('Open Sans', fontSize, 300)
        qApp.setFont(appFont)

        self.clipTimes = []
        self.inCut = False
        self.movieFilename = ''
        self.movieLoaded = False
        self.timeformat = 'hh:mm:ss'
        self.finalFilename = ''
        self.totalRuntime = 0

        self.initIcons()
        self.initActions()

        self.toolbar = QToolBar(floatable=False, movable=False, iconSize=QSize(40, 36))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toolbar.setStyleSheet('''QToolBar { spacing:10px; }
            QToolBar QToolButton { border:1px solid transparent; min-width:95px; font-size:11pt; font-weight:400;
                border-radius:5px; padding:1px 2px; color:#444; }
            QToolBar QToolButton:hover { border:1px inset #6A4572; color:#6A4572; background-color:rgba(255, 255, 255, 0.85); }
            QToolBar QToolButton:pressed { border:1px inset #6A4572; color:#6A4572; background-color:rgba(255, 255, 255, 0.25); }
            QToolBar QToolButton:disabled { color:#999; }''')
        self.initToolbar()

        self.appMenu, self.cliplistMenu = QMenu(), QMenu()
        self.initMenus()

        self.seekSlider = VideoSlider(parent=self, sliderMoved=self.setPosition)

        self.initNoVideo()

        self.cliplist = QListWidget(sizePolicy=QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding),
                                    contextMenuPolicy=Qt.CustomContextMenu, uniformItemSizes=True,
                                    iconSize=QSize(100, 700), dragDropMode=QAbstractItemView.InternalMove,
                                    alternatingRowColors=True, customContextMenuRequested=self.itemMenu,
                                    dragEnabled=True)
        self.cliplist.setStyleSheet('QListView { border-radius:0; border:none; border-left:1px solid #B9B9B9; ' +
                                    'border-right:1px solid #B9B9B9; } QListView::item { padding:10px 0; }')
        self.cliplist.setFixedWidth(185)
        self.cliplist.model().rowsMoved.connect(self.syncClipList)

        listHeader = QLabel(pixmap=QPixmap(MainWindow.get_path('images/clipindex.png'), 'PNG'),
                            alignment=Qt.AlignCenter)
        listHeader.setStyleSheet('''padding:5px; padding-top:8px; border:1px solid #b9b9b9;
                                    background-color:qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF,
                                    stop: 0.5 #EAEAEA, stop: 0.6 #EAEAEA stop:1 #FFF);''')

        self.runtimeLabel = QLabel('<div align="right">00:00:00</div>', textFormat=Qt.RichText)
        self.runtimeLabel.setStyleSheet('''font-family:Droid Sans Mono; font-size:10pt; color:#FFF;
                                           background:rgb(106, 69, 114) url(:images/runtime.png)
                                           no-repeat left center; padding:2px; padding-right:8px;
                                           border:1px solid #B9B9B9;''')

        self.clipindexLayout = QVBoxLayout(spacing=0)
        self.clipindexLayout.setContentsMargins(0, 0, 0, 0)
        self.clipindexLayout.addWidget(listHeader)
        self.clipindexLayout.addWidget(self.cliplist)
        self.clipindexLayout.addWidget(self.runtimeLabel)

        self.videoLayout = QHBoxLayout()
        self.videoLayout.setContentsMargins(0, 0, 0, 0)
        self.videoLayout.addWidget(self.novideoWidget)
        self.videoLayout.addLayout(self.clipindexLayout)

        self.timeCounter = QLabel('00:00:00 / 00:00:00', autoFillBackground=True, alignment=Qt.AlignCenter,
                                  sizePolicy=QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.timeCounter.setStyleSheet(
            'color:#FFF; background:#000; font-family:Droid Sans Mono; font-size:10.5pt; padding:4px;')

        videoplayerLayout = QVBoxLayout(spacing=0)
        videoplayerLayout.setContentsMargins(0, 0, 0, 0)
        videoplayerLayout.addWidget(self.videoWidget)
        videoplayerLayout.addWidget(self.timeCounter)

        self.videoplayerWidget = QWidget(self, visible=False)
        self.videoplayerWidget.setLayout(videoplayerLayout)

        self.muteButton = QPushButton(icon=self.unmuteIcon, flat=True, toolTip='Mute',
                                      statusTip='Toggle audio mute', iconSize=QSize(16, 16),
                                      cursor=Qt.PointingHandCursor, clicked=self.muteAudio)

        self.volumeSlider = QSlider(Qt.Horizontal, toolTip='Volume', statusTip='Adjust volume level',
                                    cursor=Qt.PointingHandCursor, value=50, minimum=0, maximum=100,
                                    sliderMoved=self.setVolume)

        self.menuButton = QPushButton(icon=self.menuIcon, flat=True, toolTip='Menu',
                                      statusTip='Media + application information',
                                      iconSize=QSize(24, 24), cursor=Qt.PointingHandCursor)
        self.menuButton.setMenu(self.appMenu)

        toolbarLayout = QHBoxLayout()
        toolbarLayout.addWidget(self.toolbar)
        toolbarLayout.setContentsMargins(2, 2, 2, 2)

        toolbarGroup = QGroupBox()
        toolbarGroup.setFlat(False)
        toolbarGroup.setCursor(Qt.PointingHandCursor)
        toolbarGroup.setLayout(toolbarLayout)

        toolbarGroup.setStyleSheet('''QGroupBox { background-color:rgba(0, 0, 0, 0.1);
            border:1px inset #888; border-radius:5px; }''')

        controlsLayout = QHBoxLayout(spacing=0)
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(toolbarGroup)
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.muteButton)
        controlsLayout.addWidget(self.volumeSlider)
        controlsLayout.addSpacing(1)
        controlsLayout.addWidget(self.menuButton)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 4)
        layout.addLayout(self.videoLayout)
        layout.addWidget(self.seekSlider)
        layout.addSpacing(5)
        layout.addLayout(controlsLayout)
        layout.addSpacing(2)

        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def initNoVideo(self) -> None:
        novideoImage = QLabel(alignment=Qt.AlignCenter, autoFillBackground=False,
                              pixmap=QPixmap(MainWindow.get_path('images/novideo.png'), 'PNG'),
                              sizePolicy=QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding))
        novideoImage.setBackgroundRole(QPalette.Dark)
        novideoImage.setContentsMargins(0, 20, 0, 20)
        self.novideoLabel = QLabel(alignment=Qt.AlignCenter, autoFillBackground=True,
                                   sizePolicy=QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.novideoLabel.setBackgroundRole(QPalette.Dark)
        self.novideoLabel.setContentsMargins(0, 20, 15, 60)
        novideoLayout = QVBoxLayout(spacing=0)
        novideoLayout.addWidget(novideoImage)
        novideoLayout.addWidget(self.novideoLabel, alignment=Qt.AlignTop)
        self.novideoMovie = QMovie(MainWindow.get_path('images/novideotext.gif'))
        self.novideoMovie.frameChanged.connect(self.setNoVideoText)
        self.novideoMovie.start()
        self.novideoWidget.setBackgroundRole(QPalette.Dark)
        self.novideoWidget.setLayout(novideoLayout)

    def initIcons(self) -> None:
        self.appIcon = QIcon(MainWindow.get_path('images/vidcutter.png'))
        self.openIcon = icon('fa.film', color='#444', color_active='#6A4572', scale_factor=0.9)
        self.playIcon = icon('fa.play-circle-o', color='#444', color_active='#6A4572', scale_factor=1.1)
        self.pauseIcon = icon('fa.pause-circle-o', color='#444', color_active='#6A4572', scale_factor=1.1)
        self.cutStartIcon = icon('fa.scissors', scale_factor=1.15, color='#444', color_active='#6A4572')
        endicon_normal = icon('fa.scissors', scale_factor=1.15, color='#444').pixmap(QSize(36, 36)).toImage()
        endicon_active = icon('fa.scissors', scale_factor=1.15, color='#6A4572').pixmap(QSize(36, 36)).toImage()
        self.cutEndIcon = QIcon()
        self.cutEndIcon.addPixmap(QPixmap.fromImage(endicon_normal.mirrored(horizontal=True, vertical=False)),
                                  QIcon.Normal, QIcon.Off)
        self.cutEndIcon.addPixmap(QPixmap.fromImage(endicon_active.mirrored(horizontal=True, vertical=False)),
                                  QIcon.Active, QIcon.Off)
        self.saveIcon = icon('fa.video-camera', color='#6A4572', color_active='#6A4572')
        self.muteIcon = QIcon(MainWindow.get_path('images/muted.png'))
        self.unmuteIcon = QIcon(MainWindow.get_path('images/unmuted.png'))
        self.upIcon = icon('ei.caret-up', color='#444')
        self.downIcon = icon('ei.caret-down', color='#444')
        self.removeIcon = icon('ei.remove', color='#B41D1D')
        self.removeAllIcon = icon('ei.trash', color='#B41D1D')
        self.successIcon = QIcon(MainWindow.get_path('images/success.png'))
        self.menuIcon = icon('fa.cog', color='#444', scale_factor=1.15)
        self.completePlayIcon = icon('fa.play', color='#444')
        self.completeOpenIcon = icon('fa.folder-open', color='#444')
        self.completeRestartIcon = icon('fa.retweet', color='#444')
        self.completeExitIcon = icon('fa.sign-out', color='#444')
        self.mediaInfoIcon = icon('fa.info-circle', color='#444')
        self.updateCheckIcon = icon('fa.cloud-download', color='#444')

    def initActions(self) -> None:
        self.openAction = QAction(self.openIcon, 'Open', self, statusTip='Open media file',
                                  triggered=self.openMedia)
        self.playAction = QAction(self.playIcon, 'Play', self, statusTip='Play media file',
                                  triggered=self.playMedia, enabled=False)
        self.cutStartAction = QAction(self.cutStartIcon, ' Start', self, toolTip='Start',
                                      statusTip='Set clip start marker',
                                      triggered=self.setCutStart, enabled=False)
        self.cutEndAction = QAction(self.cutEndIcon, ' End', self, toolTip='End', statusTip='Set clip end marker',
                                    triggered=self.setCutEnd, enabled=False)
        self.saveAction = QAction(self.saveIcon, 'Save', self, statusTip='Save clips to a new video file',
                                  triggered=self.cutVideo, enabled=False)
        self.moveItemUpAction = QAction(self.upIcon, 'Move up', self, statusTip='Move clip position up in list',
                                        triggered=self.moveItemUp, enabled=False)
        self.moveItemDownAction = QAction(self.downIcon, 'Move down', self, statusTip='Move clip position down in list',
                                          triggered=self.moveItemDown, enabled=False)
        self.removeItemAction = QAction(self.removeIcon, 'Remove clip', self,
                                        statusTip='Remove selected clip from list', triggered=self.removeItem,
                                        enabled=False)
        self.removeAllAction = QAction(self.removeAllIcon, 'Clear list', self, statusTip='Clear all clips from list',
                                       triggered=self.clearList, enabled=False)
        self.mediaInfoAction = QAction(self.mediaInfoIcon, 'Media information', self,
                                       statusTip='View current media file information', triggered=self.mediaInfo,
                                       enabled=False)
        self.updateCheckAction = QAction(self.updateCheckIcon, 'Check for updates...', self,
                                         statusTip='Check for application updates', triggered=self.updateCheck)
        self.aboutQtAction = QAction('About Qt', self, statusTip='About Qt', triggered=qApp.aboutQt)
        self.aboutAction = QAction('About %s' % qApp.applicationName(), self, statusTip='Credits and licensing',
                                   triggered=self.aboutInfo)

    def initToolbar(self) -> None:
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.playAction)
        self.toolbar.addAction(self.cutStartAction)
        self.toolbar.addAction(self.cutEndAction)
        self.toolbar.addAction(self.saveAction)

    def initMenus(self) -> None:
        self.appMenu.addAction(self.mediaInfoAction)
        self.appMenu.addAction(self.updateCheckAction)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.aboutQtAction)
        self.appMenu.addAction(self.aboutAction)

        self.cliplistMenu.addAction(self.moveItemUpAction)
        self.cliplistMenu.addAction(self.moveItemDownAction)
        self.cliplistMenu.addSeparator()
        self.cliplistMenu.addAction(self.removeItemAction)
        self.cliplistMenu.addAction(self.removeAllAction)

    @staticmethod
    def getSpacer() -> QWidget:
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return spacer

    def setRunningTime(self, runtime: str) -> None:
        self.runtimeLabel.setText('<div align="right">%s</div>' % runtime)

    @pyqtSlot(int)
    def setNoVideoText(self) -> None:
        self.novideoLabel.setPixmap(self.novideoMovie.currentPixmap())

    def itemMenu(self, pos: QPoint) -> None:
        globalPos = self.cliplist.mapToGlobal(pos)
        self.moveItemUpAction.setEnabled(False)
        self.moveItemDownAction.setEnabled(False)
        self.removeItemAction.setEnabled(False)
        self.removeAllAction.setEnabled(False)
        index = self.cliplist.currentRow()
        if index != -1:
            if not self.inCut:
                if index > 0:
                    self.moveItemUpAction.setEnabled(True)
                if index < self.cliplist.count() - 1:
                    self.moveItemDownAction.setEnabled(True)
            if self.cliplist.count() > 0:
                self.removeItemAction.setEnabled(True)
        if self.cliplist.count() > 0:
            self.removeAllAction.setEnabled(True)
        self.cliplistMenu.exec_(globalPos)

    def moveItemUp(self) -> None:
        index = self.cliplist.currentRow()
        tmpItem = self.clipTimes[index]
        del self.clipTimes[index]
        self.clipTimes.insert(index - 1, tmpItem)
        self.renderTimes()

    def moveItemDown(self) -> None:
        index = self.cliplist.currentRow()
        tmpItem = self.clipTimes[index]
        del self.clipTimes[index]
        self.clipTimes.insert(index + 1, tmpItem)
        self.renderTimes()

    def removeItem(self) -> None:
        index = self.cliplist.currentRow()
        del self.clipTimes[index]
        if self.inCut and index == self.cliplist.count() - 1:
            self.inCut = False
            self.initMediaControls()
        self.renderTimes()

    def clearList(self) -> None:
        self.clipTimes.clear()
        self.cliplist.clear()
        self.inCut = False
        self.renderTimes()
        self.initMediaControls()

    def mediaInfo(self) -> None:
        if self.mediaPlayer.isMetaDataAvailable():
            content = '<table cellpadding="4">'
            for key in self.mediaPlayer.availableMetaData():
                val = self.mediaPlayer.metaData(key)
                if type(val) is QSize:
                    val = '%s x %s' % (val.width(), val.height())
                content += '<tr><td align="right"><b>%s:</b></td><td>%s</td></tr>\n' % (key, val)
            content += '</table>'
            mbox = QMessageBox(windowTitle='Media Information', windowIcon=self.parent.windowIcon(),
                               textFormat=Qt.RichText)
            mbox.setText('<b>%s</b>' % os.path.basename(self.mediaPlayer.currentMedia().canonicalUrl().toLocalFile()))
            mbox.setInformativeText(content)
            mbox.exec_()
        else:
            QMessageBox.critical(self.parent, 'MEDIA ERROR',
                                 '<h3>Could not probe media file.</h3>' +
                                 '<p>An error occurred while analyzing the media file for its metadata details.' +
                                 '<br/><br/><b>This DOES NOT mean there is a problem with the file and you should ' +
                                 'be able to continue using it.</b></p>')

    def aboutInfo(self) -> None:
        about_html = '''<style>
    a { color:#441d4e; text-decoration:none; font-weight:bold; }
    a:hover { text-decoration:underline; }
</style>
<div style="min-width:650px;">
<p style="font-size:26pt; font-weight:bold; color:#6A4572;">%s</p>
<p>
    <span style="font-size:13pt;"><b>Version: %s</b></span>
    <span style="font-size:10pt;position:relative;left:5px;">( %s )</span>
</p>
<p style="font-size:13px;">
    Copyright &copy; 2016 <a href="mailto:pete@ozmartians.com">Pete Alexandrou</a>
    <br/>
    Website: <a href="%s">%s</a>
</p>
<p style="font-size:13px;">
    Thanks to the folks behind the <b>Qt</b>, <b>PyQt</b> and <b>FFmpeg</b>
    projects for all their hard and much appreciated work.
</p>
<p style="font-size:11px;">
    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.
</p>
<p style="font-size:11px;">
    This software uses libraries from the <a href="https://www.ffmpeg.org">FFmpeg</a> project under the
    <a href="https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html">LGPLv2.1</a>
</p></div>''' % (qApp.applicationName(), qApp.applicationVersion(), platform.architecture()[0],
                 qApp.organizationDomain(), qApp.organizationDomain())
        QMessageBox.about(self.parent, 'About %s' % qApp.applicationName(), about_html)

    def openMedia(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self.parent, caption='Select video', directory=QDir.homePath())
        if filename != '':
            self.loadFile(filename)

    def loadFile(self, filename: str) -> None:
        self.movieFilename = filename
        if not os.path.exists(filename):
            return
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
        self.initMediaControls(True)
        self.cliplist.clear()
        self.clipTimes = []
        self.parent.setWindowTitle('%s - %s' % (qApp.applicationName(), os.path.basename(filename)))
        if not self.movieLoaded:
            self.videoLayout.replaceWidget(self.novideoWidget, self.videoplayerWidget)
            self.novideoMovie.stop()
            self.novideoMovie.deleteLater()
            self.novideoWidget.deleteLater()
            self.videoplayerWidget.show()
            self.videoWidget.show()
            self.movieLoaded = True
        if self.mediaPlayer.isVideoAvailable():
            self.mediaPlayer.setPosition(1)
        self.mediaPlayer.play()
        self.mediaPlayer.pause()

    def playMedia(self) -> None:
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
            self.playAction.setText('Play')
        else:
            self.mediaPlayer.play()
            self.playAction.setText('Pause')

    def initMediaControls(self, flag: bool = True) -> None:
        self.playAction.setEnabled(flag)
        self.saveAction.setEnabled(False)
        self.cutStartAction.setEnabled(flag)
        self.cutEndAction.setEnabled(False)
        self.mediaInfoAction.setEnabled(flag)
        if flag:
            self.seekSlider.setRestrictValue(0)

    def setPosition(self, position: int) -> None:
        self.mediaPlayer.setPosition(position)

    def positionChanged(self, progress: int) -> None:
        self.seekSlider.setValue(progress)
        currentTime = self.deltaToQTime(progress)
        totalTime = self.deltaToQTime(self.mediaPlayer.duration())
        self.timeCounter.setText(
            '%s / %s' % (currentTime.toString(self.timeformat), totalTime.toString(self.timeformat)))

    @pyqtSlot()
    def mediaStateChanged(self) -> None:
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playAction.setIcon(self.pauseIcon)
        else:
            self.playAction.setIcon(self.playIcon)

    def durationChanged(self, duration: int) -> None:
        self.seekSlider.setRange(0, duration)

    def muteAudio(self) -> None:
        if self.mediaPlayer.isMuted():
            self.muteButton.setIcon(self.unmuteIcon)
            self.muteButton.setToolTip('Mute')
        else:
            self.muteButton.setIcon(self.muteIcon)
            self.muteButton.setToolTip('Unmute')
        self.mediaPlayer.setMuted(not self.mediaPlayer.isMuted())

    def setVolume(self, volume: int) -> None:
        self.mediaPlayer.setVolume(volume)

    def toggleFullscreen(self) -> None:
        self.videoWidget.setFullScreen(not self.videoWidget.isFullScreen())

    def setCutStart(self) -> None:
        self.clipTimes.append([self.deltaToQTime(self.mediaPlayer.position()), '', self.captureImage()])
        self.cutStartAction.setDisabled(True)
        self.cutEndAction.setEnabled(True)
        self.seekSlider.setRestrictValue(self.seekSlider.value(), True)
        self.inCut = True
        self.renderTimes()

    def setCutEnd(self) -> None:
        item = self.clipTimes[len(self.clipTimes) - 1]
        selected = self.deltaToQTime(self.mediaPlayer.position())
        if selected.__lt__(item[0]):
            QMessageBox.critical(self.parent, 'Invalid END Time',
                                 'The clip end time must come AFTER it\'s start time. Please try again.')
            return
        item[1] = selected
        self.cutStartAction.setEnabled(True)
        self.cutEndAction.setDisabled(True)
        self.seekSlider.setRestrictValue(0, False)
        self.inCut = False
        self.renderTimes()

    @pyqtSlot(QModelIndex, int, int, QModelIndex, int)
    def syncClipList(self, parent: QModelIndex, start: int, end: int, destination: QModelIndex, row: int) -> None:
        if start < row:
            index = row - 1
        else:
            index = row
        clip = self.clipTimes.pop(start)
        self.clipTimes.insert(index, clip)

    def renderTimes(self) -> None:
        self.cliplist.clear()
        if len(self.clipTimes) > 4:
            self.cliplist.setFixedWidth(200)
        else:
            self.cliplist.setFixedWidth(185)
        self.totalRuntime = 0
        for item in self.clipTimes:
            endItem = ''
            if type(item[1]) is QTime:
                endItem = item[1].toString(self.timeformat)
                self.totalRuntime += item[0].msecsTo(item[1])
            listitem = QListWidgetItem()
            listitem.setTextAlignment(Qt.AlignVCenter)
            if type(item[2]) is QPixmap:
                listitem.setIcon(QIcon(item[2]))
            self.cliplist.addItem(listitem)
            marker = QLabel('''<style>b { font-size:7pt; } p { margin:2px 5px; }</style>
                            <p><b>START</b><br/>%s<br/><b>END</b><br/>%s</p>'''
                            % (item[0].toString(self.timeformat), endItem))
            marker.setStyleSheet('border:none;')
            self.cliplist.setItemWidget(listitem, marker)
            listitem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled)
        if len(self.clipTimes) and not self.inCut:
            self.saveAction.setEnabled(True)
        if self.inCut or len(self.clipTimes) == 0 or not type(self.clipTimes[0][1]) is QTime:
            self.saveAction.setEnabled(False)
        self.setRunningTime(self.deltaToQTime(self.totalRuntime).toString(self.timeformat))

    @staticmethod
    def deltaToQTime(millisecs: int) -> QTime:
        secs = millisecs / 1000
        return QTime((secs / 3600) % 60, (secs / 60) % 60, secs % 60, (secs * 1000) % 1000)

    def captureImage(self) -> QPixmap:
        frametime = self.deltaToQTime(self.mediaPlayer.position()).toString(self.timeformat)
        inputfile = self.mediaPlayer.currentMedia().canonicalUrl().toLocalFile()
        imagecap = self.videoService.capture(inputfile, frametime)
        if type(imagecap) is QPixmap:
            return imagecap

    def cutVideo(self) -> bool:
        clips = len(self.clipTimes)
        filename, filelist = '', []
        source = self.mediaPlayer.currentMedia().canonicalUrl().toLocalFile()
        _, sourceext = os.path.splitext(source)
        if clips > 0:
            self.finalFilename, _ = QFileDialog.getSaveFileName(self.parent, 'Save video', source,
                                                                'Video files (*%s)' % sourceext)
            if self.finalFilename == '':
                return False
            qApp.setOverrideCursor(Qt.BusyCursor)
            self.saveAction.setDisabled(True)
            self.showProgress(clips)
            file, ext = os.path.splitext(self.finalFilename)
            index = 1
            self.progress.setLabelText('Cutting media files...')
            qApp.processEvents()
            for clip in self.clipTimes:
                duration = self.deltaToQTime(clip[0].msecsTo(clip[1])).toString(self.timeformat)
                filename = '%s_%s%s' % (file, '{0:0>2}'.format(index), ext)
                filelist.append(filename)
                self.videoService.cut(source, filename, clip[0].toString(self.timeformat), duration)
                index += 1
            if len(filelist) > 1:
                self.joinVideos(filelist, self.finalFilename)
            else:
                QFile.remove(self.finalFilename)
                QFile.rename(filename, self.finalFilename)
            self.progress.setLabelText('Complete...')
            self.progress.setValue(100)
            qApp.processEvents()
            self.progress.close()
            self.progress.deleteLater()
            qApp.restoreOverrideCursor()
            self.complete()
            return True
        return False

    def joinVideos(self, joinlist: list, filename: str) -> None:
        listfile = os.path.normpath(os.path.join(os.path.dirname(joinlist[0]), '.vidcutter.list'))
        fobj = open(listfile, 'w')
        for file in joinlist:
            fobj.write('file \'%s\'\n' % file.replace("'", "\\'"))
        fobj.close()
        self.videoService.join(listfile, filename)
        QFile.remove(listfile)
        for file in joinlist:
            if os.path.isfile(file):
                QFile.remove(file)

    def updateCheck(self) -> None:
        self.updater = Updater()
        self.updater.updateAvailable.connect(self.updateHandler)
        self.updater.start()

    def updateHandler(self, updateExists: bool, version: str = None):
        if updateExists:
            if Updater.notify_update(self, version) == QMessageBox.AcceptRole:
                self.updater.install_update(self)
        else:
            Updater.notify_no_update(self)

    def showProgress(self, steps: int, label: str = 'Analyzing media...') -> None:
        self.progress = QProgressDialog(label, None, 0, steps, self.parent, windowModality=Qt.ApplicationModal,
                                        windowIcon=self.parent.windowIcon(), minimumDuration=0, minimumWidth=500)
        self.progress.show()
        for i in range(steps):
            self.progress.setValue(i)
            qApp.processEvents()
            time.sleep(1)

    def complete(self) -> None:
        info = QFileInfo(self.finalFilename)
        mbox = QMessageBox(windowTitle='VIDEO PROCESSING COMPLETE', minimumWidth=500, textFormat=Qt.RichText)
        mbox.setText('''
    <style>
        table.info { margin:6px; padding:4px 15px; }
        td.label { font-weight:bold; font-size:10.5pt; text-align:right; }
        td.value { font-size:10.5pt; }
    </style>
    <table class="info" cellpadding="4" cellspacing="0">
        <tr>
            <td class="label"><b>File:</b></td>
            <td class="value" nowrap>%s</td>
        </tr>
        <tr>
            <td class="label"><b>Size:</b></td>
            <td class="value">%s</td>
        </tr>
        <tr>
            <td class="label"><b>Length:</b></td>
            <td class="value">%s</td>
        </tr>
    </table><br/>''' % (
            QDir.toNativeSeparators(self.finalFilename), self.sizeof_fmt(int(info.size())),
            self.deltaToQTime(self.totalRuntime).toString(self.timeformat)))
        play = mbox.addButton('Play', QMessageBox.AcceptRole)
        play.setIcon(self.completePlayIcon)
        play.clicked.connect(self.openResult)
        fileman = mbox.addButton('Open', QMessageBox.AcceptRole)
        fileman.setIcon(self.completeOpenIcon)
        fileman.clicked.connect(self.openFolder)
        end = mbox.addButton('Exit', QMessageBox.AcceptRole)
        end.setIcon(self.completeExitIcon)
        end.clicked.connect(self.close)
        new = mbox.addButton('Restart', QMessageBox.AcceptRole)
        new.setIcon(self.completeRestartIcon)
        new.clicked.connect(self.parent.restart)
        mbox.setDefaultButton(new)
        mbox.setEscapeButton(new)
        mbox.adjustSize()
        mbox.exec_()

    def sizeof_fmt(self, num: float, suffix: chr = 'B') -> str:
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Y', suffix)

    @pyqtSlot()
    def openFolder(self) -> None:
        self.openResult(pathonly=True)

    @pyqtSlot(bool)
    def openResult(self, pathonly: bool = False) -> None:
        self.parent.restart()
        if len(self.finalFilename) and os.path.exists(self.finalFilename):
            target = self.finalFilename if not pathonly else os.path.dirname(self.finalFilename)
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))

    @pyqtSlot()
    def startNew(self) -> None:
        qApp.restoreOverrideCursor()
        self.clearList()
        self.seekSlider.setValue(0)
        self.seekSlider.setRange(0, 0)
        self.mediaPlayer.setMedia(QMediaContent())
        self.initNoVideo()
        self.videoLayout.replaceWidget(self.videoplayerWidget, self.novideoWidget)
        self.initMediaControls(False)
        self.parent.setWindowTitle('%s' % qApp.applicationName())

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.mediaPlayer.isVideoAvailable() or self.mediaPlayer.isAudioAvailable():
            if event.angleDelta().y() > 0:
                newval = self.seekSlider.value() - 1000
            else:
                newval = self.seekSlider.value() + 1000
            self.seekSlider.setValue(newval)
            self.seekSlider.setSliderPosition(newval)
            self.mediaPlayer.setPosition(newval)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.mediaPlayer.isVideoAvailable() or self.mediaPlayer.isAudioAvailable():
            addtime = 0
            if event.key() == Qt.Key_Left:
                addtime = -1000
            elif event.key() == Qt.Key_PageUp or event.key() == Qt.Key_Up:
                addtime = -10000
            elif event.key() == Qt.Key_Right:
                addtime = 1000
            elif event.key() == Qt.Key_PageDown or event.key() == Qt.Key_Down:
                addtime = 10000
            elif event.key() == Qt.Key_Enter:
                self.toggleFullscreen()
            elif event.key() == Qt.Key_Escape and self.videoWidget.isFullScreen():
                self.videoWidget.setFullScreen(False)
            if addtime != 0:
                newval = self.seekSlider.value() + addtime
                self.seekSlider.setValue(newval)
                self.seekSlider.setSliderPosition(newval)
                self.mediaPlayer.setPosition(newval)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.BackButton and self.cutStartAction.isEnabled():
            self.setCutStart()
            event.accept()
        elif event.button() == Qt.ForwardButton and self.cutEndAction.isEnabled():
            self.setCutEnd()
            event.accept()
        else:
            super(VidCutter, self).mousePressEvent(event)

    @pyqtSlot(QMediaPlayer.Error)
    def handleError(self, error: QMediaPlayer.Error) -> None:
        qApp.restoreOverrideCursor()
        self.startNew()
        if error == QMediaPlayer.ResourceError:
            QMessageBox.critical(self.parent, 'INVALID MEDIA', 'Invalid media file detected at:<br/><br/><b>%s</b><br/><br/>%s'
                                 % (self.movieFilename, self.mediaPlayer.errorString()))
        else:
            QMessageBox.critical(self.parent, 'ERROR NOTIFICATION', self.mediaPlayer.errorString())

    def closeEvent(self, event: QCloseEvent) -> None:
        self.parent.closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.init_cutter()
        self.setWindowTitle('%s' % qApp.applicationName())
        self.setContentsMargins(0, 0, 0, 0)
        self.statusBar().setStyleSheet('border:none;')
        self.statusBar().showMessage('Ready')
        self.setAcceptDrops(True)
        self.setMinimumSize(900, 650)
        self.resize(900, 650)
        self.show()
        if sys.platform == 'win32' and not self.ffmpeg_check():
            if not self.ffmpeg_install():
                pass
                # TODO: handle error on Windows with no ffmpeg.zip
        try:
            if len(sys.argv) >= 2:
                self.cutter.loadFile(sys.argv[1])
        except FileNotFoundError | PermissionError:
            QMessageBox.critical(self, 'Error loading file', sys.exc_info()[0])
            qApp.restoreOverrideCursor()
            self.cutter.startNew()

    def init_cutter(self) -> None:
        self.cutter = VidCutter(self)
        qApp.setWindowIcon(self.cutter.appIcon)
        self.setCentralWidget(self.cutter)

    def ffmpeg_install(self) -> bool:
        ffmpeg_zip = MainWindow.get_path('bin/ffmpeg.zip', override=True)
        if os.path.exists(ffmpeg_zip):
            with ZipFile(ffmpeg_zip) as archive:
                archive.extract('ffmpeg.exe', path=os.path.dirname(ffmpeg_zip))
            os.remove(ffmpeg_zip)
            return True
        return False

    def ffmpeg_check(self) -> bool:
        return os.path.exists(MainWindow.get_path('bin/ffmpeg.exe', override=True))

    def restart(self):
        self.cutter.deleteLater()
        self.init_cutter()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        filename = event.mimeData().urls()[0].toLocalFile()
        self.cutter.loadFile(filename)
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.cutter.deleteLater()
        self.deleteLater()
        qApp.quit()

    @staticmethod
    def get_path(path: str = None, override: bool = False) -> str:
        if override:
            if getattr(sys, 'frozen', False):
                return os.path.join(sys._MEIPASS, path)
            return os.path.join(QFileInfo(__file__).absolutePath(), path)
        return ':%s' % path

    @staticmethod
    def get_style(label: bool = False) -> str:
        style = 'Fusion'
        if sys.platform.startswith('linux'):
            installed_styles = QStyleFactory.keys()
            for stl in ('Breeze', 'GTK+'):
                if stl.lower() in map(str.lower, installed_styles):
                    style = stl
                    break
        elif sys.platform == 'darwin':
            style = 'Macintosh'
        return style

    @staticmethod
    def get_version(filename: str = '__init__.py') -> str:
        with open(MainWindow.get_path(filename, override=True), 'r') as initfile:
            for line in initfile.readlines():
                m = re.match('__version__ *= *[\'](.*)[\']', line)
                if m:
                    return m.group(1)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('VidCutter')
    app.setApplicationVersion(MainWindow.get_version())
    app.setOrganizationDomain('http://vidcutter.ozmartians.com')
    app.setQuitOnLastWindowClosed(True)
    vidcutter = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
