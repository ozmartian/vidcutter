#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import signal
import sys
import time
import warnings

from PyQt5.QtCore import QDir, QEvent, QFile, QFileInfo, QModelIndex, QObject, QPoint, QSize, Qt, QTime, QUrl, pyqtSlot
from PyQt5.QtGui import (QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent, QFont, QFontDatabase, QIcon,
                         QKeyEvent, QMouseEvent, QMovie, QPalette, QPixmap, QWheelEvent)
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QApplication, QFileDialog, QHBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QMainWindow, QMenu, QMessageBox, QProgressDialog, QPushButton,
                             QSizePolicy, QSpacerItem, QSlider, QStyle, QToolBar, QVBoxLayout, QWidget, qApp)

from vidcutter.videoservice import VideoService
from vidcutter.videoslider import VideoSlider
import vidcutter.resources


signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)
warnings.filterwarnings('ignore')


__version__ = '1.6.0'


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
        self.parent = parent
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videoWidget = VideoWidget()
        self.videoService = VideoService(self)

        QFontDatabase.addApplicationFont(os.path.join(self.getAppPath(), 'fonts', 'DroidSansMono.ttf'))
        QFontDatabase.addApplicationFont(os.path.join(self.getAppPath(), 'fonts', 'HelveticaNeue.ttf'))
        qApp.setFont(QFont('Helvetica Neue', 10))

        self.clipTimes = []
        self.inCut = False
        self.movieFilename = ''
        self.movieLoaded = False
        self.timeformat = 'hh:mm:ss'
        self.finalFilename = ''
        self.totalRuntime = 0

        self.initIcons()
        self.initActions()

        self.toolbar = QToolBar(floatable=False, movable=False, iconSize=QSize(28, 28),
                                toolButtonStyle=Qt.ToolButtonTextUnderIcon,
                                styleSheet='QToolBar QToolButton { min-width:82px; margin-left:10px; margin-right:10px; font-size:14px; }')
        self.initToolbar()

        self.aboutMenu, self.cliplistMenu = QMenu(), QMenu()
        self.initMenus()

        self.seekSlider = VideoSlider(parent=self, sliderMoved=self.setPosition)
        self.seekSlider.installEventFilter(self)

        self.initNoVideo()

        self.cliplist = QListWidget(sizePolicy=QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding),
                                    contextMenuPolicy=Qt.CustomContextMenu, uniformItemSizes=True,
                                    iconSize=QSize(100, 700), dragDropMode=QAbstractItemView.InternalMove,
                                    alternatingRowColors=True, customContextMenuRequested=self.itemMenu,
                                    dragEnabled=True, styleSheet='QListView::item { margin:10px 5px; }')
        self.cliplist.setFixedWidth(185)
        self.cliplist.model().rowsMoved.connect(self.syncClipList)

        listHeader = QLabel(pixmap=QPixmap(os.path.join(self.getAppPath(), 'images', 'clipindex.png'), 'PNG'),
                            alignment=Qt.AlignCenter)
        listHeader.setStyleSheet('''padding:5px; padding-top:8px; border:1px solid #b9b9b9; border-bottom:none;
                                    background-color:qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF,
                                    stop: 0.5 #EAEAEA, stop: 0.6 #EAEAEA stop:1 #FFF);''')

        self.runtimeLabel = QLabel('<div align="right">00:00:00</div>', textFormat=Qt.RichText)
        self.runtimeLabel.setStyleSheet('''font-family:Droid Sans Mono; font-size:10pt; color:#FFF;
                                           background:rgb(106, 69, 114) url(:images/runtime.png)
                                           no-repeat left center; padding:2px; padding-right:8px;
                                           border:1px solid #b9b9b9; border-top:none;''')

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
        self.timeCounter.setStyleSheet('color:#FFF; background:#000; font-family:Droid Sans Mono; font-size:10.5pt; padding:4px;')

        videoplayerLayout = QVBoxLayout(spacing=0)
        videoplayerLayout.setContentsMargins(0, 0, 0, 0)
        videoplayerLayout.addWidget(self.videoWidget)
        videoplayerLayout.addWidget(self.timeCounter)

        self.videoplayerWidget = QWidget(self, visible=False)
        self.videoplayerWidget.setLayout(videoplayerLayout)

        self.menuButton = QPushButton(icon=self.aboutIcon, flat=True, toolTip='Menu', statusTip='Media + application information',
                                      iconSize=QSize(24, 24), cursor=Qt.PointingHandCursor)
        self.menuButton.setMenu(self.aboutMenu)

        self.muteButton = QPushButton(icon=self.unmuteIcon, flat=True, toolTip='Mute',
                                      statusTip='Toggle audio mute',
                                      cursor=Qt.PointingHandCursor, clicked=self.muteAudio)

        self.volumeSlider = QSlider(Qt.Horizontal, toolTip='Volume', statusTip='Adjust volume level',
                                    cursor=Qt.PointingHandCursor, value=50,
                                    sizePolicy=QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum),
                                    minimum=0, maximum=100, sliderMoved=self.setVolume)
        self.volumeSlider.setStyleSheet('''QSlider::groove:horizontal { position:absolute; top:20px; }
                                           QSlider::sub-page:horizontal { border:1px outset #6A4572; background:#6A4572; margin:2px; }
                                           QSlider::handle:horizontal { image: url(:images/knob.png) no-repeat center center; width:20px; }''')

        self.saveAction = QPushButton(self.parent, icon=self.saveIcon, text='Save Video', flat=True, toolTip='Save Video',
                                      clicked=self.cutVideo, cursor=Qt.PointingHandCursor, iconSize=QSize(30, 30),
                                      statusTip='Cut and join media bits to form new media file as per the Clip Index', enabled=False)
        self.saveAction.setStyleSheet('''QPushButton { color:#FFF; padding:8px; font-size:12pt;
                                            border:1px inset #481953; border-radius:4px;
                                            background-color:rgb(106, 69, 114); }
                                         QPushButton:!enabled { background-color:rgba(0, 0, 0, 0.1);
                                            color:rgba(0, 0, 0, 0.3); border:1px inset #CDCDCD; }
                                         QPushButton:hover { background-color:rgba(255, 255, 255, 0.8); color:#444; }
                                         QPushButton:pressed { background-color:rgba(218, 218, 219, 0.8); color:#444; }''')

        controlsLayout = QHBoxLayout()
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.toolbar)
        controlsLayout.addSpacerItem(QSpacerItem(20, 1))
        controlsLayout.addWidget(self.saveAction)
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.muteButton)
        controlsLayout.addWidget(self.volumeSlider, Qt.AlignVCenter)
        controlsLayout.addSpacing(1)
        controlsLayout.addWidget(self.menuButton)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 4)
        layout.addLayout(self.videoLayout)
        layout.addWidget(self.seekSlider)
        layout.addLayout(controlsLayout)

        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def initNoVideo(self) -> None:
        novideoImage = QLabel(alignment=Qt.AlignCenter, autoFillBackground=False,
                              pixmap=QPixmap(os.path.join(self.getAppPath(), 'images', 'novideo.png'), 'PNG'),
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
        self.novideoMovie = QMovie(os.path.join(self.getAppPath(), 'images', 'novideotext.gif'))
        self.novideoMovie.frameChanged.connect(self.setNoVideoText)
        self.novideoMovie.start()
        self.novideoWidget = QWidget(self, autoFillBackground=True)
        self.novideoWidget.setBackgroundRole(QPalette.Dark)
        self.novideoWidget.setLayout(novideoLayout)

    def initIcons(self) -> None:
        self.appIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'vidcutter.png'))
        self.openIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'addmedia.png'))
        self.playIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'play.png'))
        self.pauseIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'pause.png'))
        self.cutStartIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'cut-start.png'))
        self.cutEndIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'cut-end.png'))
        self.saveIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'save.png'))
        self.muteIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'muted.png'))
        self.unmuteIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'unmuted.png'))
        self.upIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'up.png'))
        self.downIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'down.png'))
        self.removeIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'remove.png'))
        self.removeAllIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'remove-all.png'))
        self.successIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'success.png'))
        self.aboutIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'about.png'))
        self.completePlayIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'complete-play.png'))
        self.completeOpenIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'complete-open.png'))
        self.completeRestartIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'complete-restart.png'))
        self.completeExitIcon = QIcon(os.path.join(self.getAppPath(), 'images', 'complete-exit.png'))

    def initActions(self) -> None:
        self.openAction = QAction(self.openIcon, 'Add Media', self, statusTip='Add source media file',
                                  triggered=self.openFile)
        self.playAction = QAction(self.playIcon, 'Play Media', self, statusTip='Play media file',
                                  triggered=self.playVideo, enabled=False)
        self.cutStartAction = QAction(self.cutStartIcon, 'Set Start', self, toolTip='Set Start',
                                      statusTip='Start from current media position', triggered=self.cutStart, enabled=False)
        self.cutEndAction = QAction(self.cutEndIcon, 'Set End', self, toolTip='Set End',
                                      statusTip='End at current media position', triggered=self.cutEnd, enabled=False)
        self.moveItemUpAction = QAction(self.upIcon, 'Move Up', self, statusTip='Move clip position up in list',
                                        triggered=self.moveItemUp, enabled=False)
        self.moveItemDownAction = QAction(self.downIcon, 'Move Down', self, statusTip='Move clip position down in list',
                                          triggered=self.moveItemDown, enabled=False)
        self.removeItemAction = QAction(self.removeIcon, 'Remove clip', self,
                                        statusTip='Remove selected clip from list', triggered=self.removeItem,
                                        enabled=False)
        self.removeAllAction = QAction(self.removeAllIcon, 'Clear list', self, statusTip='Clear all clips from list',
                                       triggered=self.clearList, enabled=False)
        self.aboutAction = QAction('About %s' % qApp.applicationName(), self, statusTip='Credits and licensing',
                                   triggered=self.aboutInfo)
        self.aboutQtAction = QAction('About Qt', self, statusTip='About Qt', triggered=qApp.aboutQt)
        self.mediaInfoAction = QAction('Media Information', self, statusTip='View current media codec information',
                                       triggered=self.mediaInfo, enabled=False)

    def initToolbar(self) -> None:
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.playAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.cutStartAction)
        self.toolbar.addAction(self.cutEndAction)
        self.toolbar.addSeparator()

    def initMenus(self) -> None:
        self.aboutMenu.addAction(self.mediaInfoAction)
        self.aboutMenu.addSeparator()
        self.aboutMenu.addAction(self.aboutQtAction)
        self.aboutMenu.addAction(self.aboutAction)
        self.cliplistMenu.addAction(self.moveItemUpAction)
        self.cliplistMenu.addAction(self.moveItemDownAction)
        self.cliplistMenu.addSeparator()
        self.cliplistMenu.addAction(self.removeItemAction)
        self.cliplistMenu.addAction(self.removeAllAction)

    def setRunningTime(self, runtime: str) -> None:
        self.runtimeLabel.setText('<div align="right">%s</div>' % runtime)

    @pyqtSlot(int)
    def setNoVideoText(self, frame: int) -> None:
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
            QMessageBox.critical(self.parent, 'Could not retrieve media information',
                                 '''There was a problem in tring to retrieve media information.
                                    This DOES NOT mean there is a problem with the file and you should
                                    be able to continue using it.''')

    def aboutInfo(self) -> None:
        about_html = '''<style>
    a { color:#441d4e; text-decoration:none; font-weight:bold; }
    a:hover { text-decoration:underline; }
</style>
<p style="font-size:26pt; font-weight:bold;">%s</p>
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
</p>''' % (qApp.applicationName(), qApp.applicationVersion(), platform.architecture()[0],
           qApp.organizationDomain(), qApp.organizationDomain())
        QMessageBox.about(self.parent, 'About %s' % qApp.applicationName(), about_html)

    def openFile(self) -> None:
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

    def playVideo(self) -> None:
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
            self.playAction.setText('Play Video')
        else:
            self.mediaPlayer.play()
            self.playAction.setText('Pause Video')

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
        self.timeCounter.setText('%s / %s' % (currentTime.toString(self.timeformat), totalTime.toString(self.timeformat)))

    @pyqtSlot()
    def mediaStateChanged(self) -> None:
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playAction.setIcon(self.pauseIcon)
        else:
            self.playAction.setIcon(self.playIcon)

    def durationChanged(self, duration: int) -> None:
        self.seekSlider.setRange(0, duration)

    def muteAudio(self, muted: bool) -> None:
        if self.mediaPlayer.isMuted():
            self.mediaPlayer.setMuted(not self.mediaPlayer.isMuted())
            self.muteButton.setIcon(self.unmuteIcon)
            self.muteButton.setToolTip('Mute')
        else:
            self.mediaPlayer.setMuted(not self.mediaPlayer.isMuted())
            self.muteButton.setIcon(self.muteIcon)
            self.muteButton.setToolTip('Unmute')

    def setVolume(self, volume: int) -> None:
        self.mediaPlayer.setVolume(volume)

    def toggleFullscreen(self) -> None:
        self.videoWidget.setFullScreen(not self.videoWidget.isFullScreen())

    def cutStart(self) -> None:
        self.clipTimes.append([self.deltaToQTime(self.mediaPlayer.position()), '', self.captureImage()])
        self.cutStartAction.setDisabled(True)
        self.cutEndAction.setEnabled(True)
        self.seekSlider.setRestrictValue(self.seekSlider.value() + 1000)
        self.mediaPlayer.setPosition(self.seekSlider.restrictValue)
        self.inCut = True
        self.renderTimes()

    def cutEnd(self) -> None:
        item = self.clipTimes[len(self.clipTimes) - 1]
        selected = self.deltaToQTime(self.mediaPlayer.position())
        if selected.__lt__(item[0]):
            QMessageBox.critical(self.parent, 'Invalid END Time',
                                 'The clip end time must come AFTER it\'s start time. Please try again.')
            return
        item[1] = selected
        self.cutStartAction.setEnabled(True)
        self.cutEndAction.setDisabled(True)
        self.seekSlider.setRestrictValue(0)
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
        self.seekSlider.setCutMode(self.inCut)
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
            marker = QLabel('''<style>b { font-size:8pt; } p { margin:5px; }</style>
                            <p><b>START</b><br/>%s</p><p><b>END</b><br/>%s</p>'''
                            % (item[0].toString(self.timeformat), endItem))
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

    def captureImage(self) -> None:
        frametime = self.deltaToQTime(self.mediaPlayer.position()).addSecs(1).toString(self.timeformat)
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
            self.finalFilename, _ = QFileDialog.getSaveFileName(self.parent, 'Save video', source, 'Video files (*%s)' % sourceext)
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
            qApp.processEvents()
            self.progress.close()
            self.progress.deleteLater()
            # self.saveAction.setEnabled(True)
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
        try:
            QFile.remove(listfile)
            for file in joinlist:
                if os.path.isfile(file):
                    QFile.remove(file)
        except:
            pass

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
        mbox = QMessageBox(windowTitle='Success', windowIcon=self.parent.windowIcon(), minimumWidth=500,
                           iconPixmap=self.successIcon.pixmap(48, 49), textFormat=Qt.RichText)
        mbox.setText('''
<style>
    table.info { margin:8px; padding:4px 15px; }
    td.label { font-weight:bold; font-size:9pt; text-align:right; background-color:#444; color:#FFF; }
    td.value { background-color:#FFF !important; font-size:10pt; }
</style>
<p>Your video was successfully created.</p>
<p align="center">
    <table class="info" cellpadding="6" cellspacing="0">
        <tr>
            <td class="label"><b>Filename</b></td>
            <td class="value" nowrap>%s</td>
        </tr>
        <tr>
            <td class="label"><b>Size</b></td>
            <td class="value">%s</td>
        </tr>
        <tr>
            <td class="label"><b>Runtime</b></td>
            <td class="value">%s</td>
        </tr>
    </table>
</p>
<p>How would you like to proceed?</p>''' % (QDir.toNativeSeparators(self.finalFilename), self.sizeof_fmt(int(info.size())),
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
        new.clicked.connect(self.startNew)
        mbox.setDefaultButton(new)
        mbox.setEscapeButton(new)
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
        self.startNew()
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
            self.cutStart()
            event.accept()
        elif event.button() == Qt.ForwardButton and self.cutEndAction.isEnabled():
            self.cutEnd()
            event.accept()
        else:
            super(VidCutter, self).mousePressEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonRelease and isinstance(obj, VideoSlider):
            if obj.objectName() == 'VideoSlider' and (
                        self.mediaPlayer.isVideoAvailable() or self.mediaPlayer.isAudioAvailable()):
                obj.setValue(QStyle.sliderValueFromPosition(obj.minimum(), obj.maximum(), event.x(), obj.width()))
                self.mediaPlayer.setPosition(obj.sliderPosition())
        return QWidget.eventFilter(self, obj, event)

    @pyqtSlot(QMediaPlayer.Error)
    def handleError(self, error: QMediaPlayer.Error) -> None:
        qApp.restoreOverrideCursor()
        self.startNew()
        if error == QMediaPlayer.ResourceError:
            QMessageBox.critical(self.parent, 'Error', 'Invalid media file detected at:<br/><br/><b>%s</b><br/><br/>%s'
                                 % (self.movieFilename, self.mediaPlayer.errorString()))
        else:
            QMessageBox.critical(self.parent, 'Error', self.mediaPlayer.errorString())

    def getAppPath(self) -> str:
        return ':'

    def closeEvent(self, event: QCloseEvent) -> None:
        self.parent.closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.statusBar().showMessage('Ready')
        self.cutter = VidCutter(self)
        self.setCentralWidget(self.cutter)
        self.setAcceptDrops(True)
        self.setWindowTitle('%s' % qApp.applicationName())
        self.setWindowIcon(self.cutter.appIcon)
        self.setMinimumSize(900, 650)
        self.resize(900, 650)
        try:
            if len(sys.argv) >= 2:
                self.cutter.loadFile(sys.argv[1])
        except:
            QMessageBox.critical(self, 'Error loading file', sys.exc_info()[0])
            qApp.restoreOverrideCursor()
            self.cutter.startNew()

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


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName('VidCutter')
    app.setApplicationVersion(__version__)
    app.setOrganizationDomain('http://vidcutter.ozmartians.com')
    app.setQuitOnLastWindowClosed(True)
    vidcutter = MainWindow()
    vidcutter.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
