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

import logging
import os
import re
import sys
import time
from datetime import timedelta
from functools import partial
from typing import Callable, List, Optional, Union

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QBuffer, QByteArray, QDir, QFile, QFileInfo, QModelIndex, QPoint, QSize,
                          Qt, QTextStream, QTime, QTimer, QUrl)
from PyQt5.QtGui import QDesktopServices, QFont, QFontDatabase, QIcon, QKeyEvent, QPixmap, QShowEvent
from PyQt5.QtWidgets import (QAction, qApp, QApplication, QDialog, QFileDialog, QFrame, QGroupBox, QHBoxLayout, QLabel,
                             QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton, QSizePolicy, QStyleFactory,
                             QVBoxLayout, QWidget)

import sip

# noinspection PyUnresolvedReferences
from vidcutter import resources
from vidcutter.about import About
from vidcutter.changelog import Changelog
from vidcutter.mediainfo import MediaInfo
from vidcutter.mediastream import StreamSelector
from vidcutter.settings import SettingsDialog
from vidcutter.updater import Updater
from vidcutter.videolist import VideoList
from vidcutter.videoslider import VideoSlider
from vidcutter.videosliderwidget import VideoSliderWidget
from vidcutter.videostyle import VideoStyleDark, VideoStyleLight

from vidcutter.libs.config import Config, InvalidMediaException, VideoFilter
from vidcutter.libs.mpvwidget import mpvWidget
from vidcutter.libs.munch import Munch
from vidcutter.libs.notifications import JobCompleteNotification
from vidcutter.libs.taskbarprogress import TaskbarProgress
from vidcutter.libs.videoservice import VideoService
from vidcutter.libs.widgets import (ClipErrorsDialog, VCBlinkText, VCDoubleInputDialog, VCFilterMenuAction,
                                    VCFrameCounter, VCInputDialog, VCMessageBox, VCProgressDialog, VCTimeCounter,
                                    VCToolBarButton, VCVolumeSlider)

import vidcutter


class VideoCutter(QWidget):
    errorOccurred = pyqtSignal(str)

    timeformat = 'hh:mm:ss.zzz'
    runtimeformat = 'hh:mm:ss'

    def __init__(self, parent: QMainWindow):
        super(VideoCutter, self).__init__(parent)
        self.setObjectName('videocutter')
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        self.theme = self.parent.theme
        self.workFolder = self.parent.WORKING_FOLDER
        self.settings = self.parent.settings
        self.filter_settings = Config.filter_settings()
        self.currentMedia, self.mediaAvailable, self.mpvError = None, False, False
        self.projectDirty, self.projectSaved, self.debugonstart = False, False, False
        self.smartcut_monitor, self.notify = None, None
        self.fonts = []

        self.initTheme()
        self.updater = Updater(self.parent)

        self.seekSlider = VideoSlider(self)
        self.seekSlider.sliderMoved.connect(self.setPosition)
        self.sliderWidget = VideoSliderWidget(self, self.seekSlider)
        self.sliderWidget.setLoader(True)

        self.taskbar = TaskbarProgress(self.parent)

        self.clipTimes = []
        self.inCut, self.newproject = False, False
        self.finalFilename = ''
        self.totalRuntime, self.frameRate = 0, 0
        self.notifyInterval = 1000

        self.createChapters = self.settings.value('chapters', 'on', type=str) in {'on', 'true'}
        self.enableOSD = self.settings.value('enableOSD', 'on', type=str) in {'on', 'true'}
        self.hardwareDecoding = self.settings.value('hwdec', 'on', type=str) in {'on', 'auto'}
        self.enablePBO = self.settings.value('enablePBO', 'off', type=str) in {'on', 'true'}
        self.keepRatio = self.settings.value('aspectRatio', 'keep', type=str) == 'keep'
        self.keepClips = self.settings.value('keepClips', 'off', type=str) in {'on', 'true'}
        self.nativeDialogs = self.settings.value('nativeDialogs', 'on', type=str) in {'on', 'true'}
        self.indexLayout = self.settings.value('indexLayout', 'right', type=str)
        self.timelineThumbs = self.settings.value('timelineThumbs', 'on', type=str) in {'on', 'true'}
        self.showConsole = self.settings.value('showConsole', 'off', type=str) in {'on', 'true'}
        self.smartcut = self.settings.value('smartcut', 'off', type=str) in {'on', 'true'}
        self.level1Seek = self.settings.value('level1Seek', 2, type=float)
        self.level2Seek = self.settings.value('level2Seek', 5, type=float)
        self.verboseLogs = self.parent.verboseLogs
        self.lastFolder = self.settings.value('lastFolder', QDir.homePath(), type=str)

        self.videoService = VideoService(self.settings, self)
        self.videoService.progress.connect(self.seekSlider.updateProgress)
        self.videoService.finished.connect(self.smartmonitor)
        self.videoService.error.connect(self.completeOnError)
        self.videoService.addScenes.connect(self.addScenes)

        self.project_files = {
            'edl': re.compile(r'(\d+(?:\.?\d+)?)\t(\d+(?:\.?\d+)?)\t([01])'),
            'vcp': re.compile(r'(\d+(?:\.?\d+)?)\t(\d+(?:\.?\d+)?)\t([01])\t(".*")$')
        }

        self._initIcons()
        self._initActions()

        self.appmenu = QMenu(self.parent)
        self.clipindex_removemenu, self.clipindex_contextmenu = QMenu(self), QMenu(self)

        self._initMenus()
        self._initNoVideo()

        self.cliplist = VideoList(self)
        self.cliplist.customContextMenuRequested.connect(self.itemMenu)
        self.cliplist.currentItemChanged.connect(self.selectClip)
        self.cliplist.model().rowsInserted.connect(self.setProjectDirty)
        self.cliplist.model().rowsRemoved.connect(self.setProjectDirty)
        self.cliplist.model().rowsMoved.connect(self.setProjectDirty)
        self.cliplist.model().rowsMoved.connect(self.syncClipList)

        self.listHeaderButtonL = QPushButton(self)
        self.listHeaderButtonL.setObjectName('listheaderbutton-left')
        self.listHeaderButtonL.setFlat(True)
        self.listHeaderButtonL.clicked.connect(self.setClipIndexLayout)
        self.listHeaderButtonL.setCursor(Qt.PointingHandCursor)
        self.listHeaderButtonL.setFixedSize(14, 14)
        self.listHeaderButtonL.setToolTip('Move to left')
        self.listHeaderButtonL.setStatusTip('Move the Clip Index list to the left side of player')
        self.listHeaderButtonR = QPushButton(self)
        self.listHeaderButtonR.setObjectName('listheaderbutton-right')
        self.listHeaderButtonR.setFlat(True)
        self.listHeaderButtonR.clicked.connect(self.setClipIndexLayout)
        self.listHeaderButtonR.setCursor(Qt.PointingHandCursor)
        self.listHeaderButtonR.setFixedSize(14, 14)
        self.listHeaderButtonR.setToolTip('Move to right')
        self.listHeaderButtonR.setStatusTip('Move the Clip Index list to the right side of player')
        listheaderLayout = QHBoxLayout()
        listheaderLayout.setContentsMargins(6, 5, 6, 5)
        listheaderLayout.addWidget(self.listHeaderButtonL)
        listheaderLayout.addStretch(1)
        listheaderLayout.addWidget(self.listHeaderButtonR)
        self.listheader = QWidget(self)
        self.listheader.setObjectName('listheader')
        self.listheader.setFixedWidth(self.cliplist.width())
        self.listheader.setLayout(listheaderLayout)
        self._initClipIndexHeader()

        self.runtimeLabel = QLabel('<div align="right">00:00:00</div>', self)
        self.runtimeLabel.setObjectName('runtimeLabel')
        self.runtimeLabel.setToolTip('total runtime: 00:00:00')
        self.runtimeLabel.setStatusTip('total running time: 00:00:00')

        self.clipindex_add = QPushButton(self)
        self.clipindex_add.setObjectName('clipadd')
        self.clipindex_add.clicked.connect(self.addExternalClips)
        self.clipindex_add.setToolTip('Add clips')
        self.clipindex_add.setStatusTip('Add one or more files to an existing project or an empty list if you are only '
                                        'joining files')
        self.clipindex_add.setCursor(Qt.PointingHandCursor)
        self.clipindex_remove = QPushButton(self)
        self.clipindex_remove.setObjectName('clipremove')
        self.clipindex_remove.setToolTip('Remove clips')
        self.clipindex_remove.setStatusTip('Remove clips from your index')
        self.clipindex_remove.setLayoutDirection(Qt.RightToLeft)
        self.clipindex_remove.setMenu(self.clipindex_removemenu)
        self.clipindex_remove.setCursor(Qt.PointingHandCursor)
        if sys.platform in {'win32', 'darwin'}:
            self.clipindex_add.setStyle(QStyleFactory.create('Fusion'))
            self.clipindex_remove.setStyle(QStyleFactory.create('Fusion'))

        clipindex_layout = QHBoxLayout()
        clipindex_layout.setSpacing(1)
        clipindex_layout.setContentsMargins(0, 0, 0, 0)
        clipindex_layout.addWidget(self.clipindex_add)
        clipindex_layout.addSpacing(1)
        clipindex_layout.addWidget(self.clipindex_remove)
        clipindexTools = QWidget(self)
        clipindexTools.setObjectName('clipindextools')
        clipindexTools.setLayout(clipindex_layout)

        self.clipindexLayout = QVBoxLayout()
        self.clipindexLayout.setSpacing(0)
        self.clipindexLayout.setContentsMargins(0, 0, 0, 0)
        self.clipindexLayout.addWidget(self.listheader)
        self.clipindexLayout.addWidget(self.cliplist)
        self.clipindexLayout.addWidget(self.runtimeLabel)
        self.clipindexLayout.addSpacing(3)
        self.clipindexLayout.addWidget(clipindexTools)

        self.videoLayout = QHBoxLayout()
        self.videoLayout.setContentsMargins(0, 0, 0, 0)
        if self.indexLayout == 'left':
            self.videoLayout.addLayout(self.clipindexLayout)
            self.videoLayout.addSpacing(10)
            self.videoLayout.addWidget(self.novideoWidget)
        else:
            self.videoLayout.addWidget(self.novideoWidget)
            self.videoLayout.addSpacing(10)
            self.videoLayout.addLayout(self.clipindexLayout)

        self.timeCounter = VCTimeCounter(self)
        self.timeCounter.timeChanged.connect(lambda newtime: self.setPosition(newtime.msecsSinceStartOfDay()))
        self.frameCounter = VCFrameCounter(self)
        self.frameCounter.setReadOnly(True)

        countersLayout = QHBoxLayout()
        countersLayout.setContentsMargins(0, 0, 0, 0)
        countersLayout.addStretch(1)
        # noinspection PyArgumentList
        countersLayout.addWidget(QLabel('TIME:', objectName='tcLabel'))
        countersLayout.addWidget(self.timeCounter)
        countersLayout.addStretch(1)
        # noinspection PyArgumentList
        countersLayout.addWidget(QLabel('FRAME:', objectName='fcLabel'))
        countersLayout.addWidget(self.frameCounter)
        countersLayout.addStretch(1)

        countersWidget = QWidget(self)
        countersWidget.setObjectName('counterwidgets')
        countersWidget.setContentsMargins(0, 0, 0, 0)
        countersWidget.setLayout(countersLayout)
        countersWidget.setMaximumHeight(28)

        self.mpvWidget = self.getMPV(self)

        self.videoplayerLayout = QVBoxLayout()
        self.videoplayerLayout.setSpacing(0)
        self.videoplayerLayout.setContentsMargins(0, 0, 0, 0)
        self.videoplayerLayout.addWidget(self.mpvWidget)
        self.videoplayerLayout.addWidget(countersWidget)

        self.videoplayerWidget = QFrame(self)
        self.videoplayerWidget.setObjectName('videoplayer')
        self.videoplayerWidget.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.videoplayerWidget.setLineWidth(0)
        self.videoplayerWidget.setMidLineWidth(0)
        self.videoplayerWidget.setVisible(False)
        self.videoplayerWidget.setLayout(self.videoplayerLayout)

        # noinspection PyArgumentList
        self.thumbnailsButton = QPushButton(self, flat=True, checkable=True, objectName='thumbnailsButton',
                                            statusTip='Toggle timeline thumbnails', cursor=Qt.PointingHandCursor,
                                            toolTip='Toggle thumbnails')
        self.thumbnailsButton.setFixedSize(32, 29 if self.theme == 'dark' else 31)
        self.thumbnailsButton.setChecked(self.timelineThumbs)
        self.thumbnailsButton.toggled.connect(self.toggleThumbs)
        if self.timelineThumbs:
            self.seekSlider.setObjectName('nothumbs')

        # noinspection PyArgumentList
        self.osdButton = QPushButton(self, flat=True, checkable=True, objectName='osdButton', toolTip='Toggle OSD',
                                     statusTip='Toggle on-screen display', cursor=Qt.PointingHandCursor)
        self.osdButton.setFixedSize(31, 29 if self.theme == 'dark' else 31)
        self.osdButton.setChecked(self.enableOSD)
        self.osdButton.toggled.connect(self.toggleOSD)

        # noinspection PyArgumentList
        self.consoleButton = QPushButton(self, flat=True, checkable=True, objectName='consoleButton',
                                         statusTip='Toggle console window', toolTip='Toggle console',
                                         cursor=Qt.PointingHandCursor)
        self.consoleButton.setFixedSize(31, 29 if self.theme == 'dark' else 31)
        self.consoleButton.setChecked(self.showConsole)
        self.consoleButton.toggled.connect(self.toggleConsole)
        if self.showConsole:
            self.mpvWidget.setLogLevel('v')
            os.environ['DEBUG'] = '1'
            self.parent.console.show()

        # noinspection PyArgumentList
        self.chaptersButton = QPushButton(self, flat=True, checkable=True, objectName='chaptersButton',
                                          statusTip='Automatically create chapters per clip', toolTip='Create chapters',
                                          cursor=Qt.PointingHandCursor)
        self.chaptersButton.setFixedSize(31, 29 if self.theme == 'dark' else 31)
        self.chaptersButton.setChecked(self.createChapters)
        self.chaptersButton.toggled.connect(self.toggleChapters)

        # noinspection PyArgumentList
        self.smartcutButton = QPushButton(self, flat=True, checkable=True, objectName='smartcutButton',
                                          toolTip='Toggle SmartCut', statusTip='Toggle frame accurate cutting',
                                          cursor=Qt.PointingHandCursor)
        self.smartcutButton.setFixedSize(32, 29 if self.theme == 'dark' else 31)
        self.smartcutButton.setChecked(self.smartcut)
        self.smartcutButton.toggled.connect(self.toggleSmartCut)

        # noinspection PyArgumentList
        self.muteButton = QPushButton(objectName='muteButton', icon=self.unmuteIcon, flat=True, toolTip='Mute',
                                      statusTip='Toggle audio mute', iconSize=QSize(16, 16), clicked=self.muteAudio,
                                      cursor=Qt.PointingHandCursor)

        # noinspection PyArgumentList
        self.volSlider = VCVolumeSlider(orientation=Qt.Horizontal, toolTip='Volume', statusTip='Adjust volume level',
                                        cursor=Qt.PointingHandCursor, value=self.parent.startupvol, minimum=0,
                                        maximum=130, minimumHeight=22, sliderMoved=self.setVolume)

        # noinspection PyArgumentList
        self.fullscreenButton = QPushButton(objectName='fullscreenButton', icon=self.fullscreenIcon, flat=True,
                                            toolTip='Toggle fullscreen', statusTip='Switch to fullscreen video',
                                            iconSize=QSize(14, 14), clicked=self.toggleFullscreen,
                                            cursor=Qt.PointingHandCursor, enabled=False)

        # noinspection PyArgumentList
        self.settingsButton = QPushButton(self, toolTip='Settings', cursor=Qt.PointingHandCursor, flat=True,
                                          statusTip='Configure application settings',
                                          objectName='settingsButton', clicked=self.showSettings)
        self.settingsButton.setFixedSize(QSize(33, 32))

        # noinspection PyArgumentList
        self.streamsButton = QPushButton(self, toolTip='Media streams', cursor=Qt.PointingHandCursor, flat=True,
                                         statusTip='Select the media streams to be included',
                                         objectName='streamsButton', clicked=self.selectStreams,
                                         enabled=False)
        self.streamsButton.setFixedSize(QSize(33, 32))

        # noinspection PyArgumentList
        self.mediainfoButton = QPushButton(self, toolTip='Media information', cursor=Qt.PointingHandCursor, flat=True,
                                           statusTip='View technical details about current media',
                                           objectName='mediainfoButton', clicked=self.mediaInfo, enabled=False)
        self.mediainfoButton.setFixedSize(QSize(33, 32))

        # noinspection PyArgumentList
        self.menuButton = QPushButton(self, toolTip='Menu', cursor=Qt.PointingHandCursor, flat=True,
                                      objectName='menuButton', clicked=self.showAppMenu, statusTip='View menu options')
        self.menuButton.setFixedSize(QSize(33, 32))

        audioLayout = QHBoxLayout()
        audioLayout.setContentsMargins(0, 0, 0, 0)
        audioLayout.addWidget(self.muteButton)
        audioLayout.addSpacing(5)
        audioLayout.addWidget(self.volSlider)
        audioLayout.addSpacing(5)
        audioLayout.addWidget(self.fullscreenButton)

        self.toolbar_open = VCToolBarButton('Open Media', 'Open and load a media file to begin', parent=self)
        self.toolbar_open.clicked.connect(self.openMedia)
        self.toolbar_play = VCToolBarButton('Play Media', 'Play currently loaded media file', parent=self)
        self.toolbar_play.setEnabled(False)
        self.toolbar_play.clicked.connect(self.playMedia)
        self.toolbar_start = VCToolBarButton('Start Clip', 'Start a new clip from the current timeline position',
                                             parent=self)
        self.toolbar_start.setEnabled(False)
        self.toolbar_start.clicked.connect(self.clipStart)
        self.toolbar_end = VCToolBarButton('End Clip', 'End a new clip at the current timeline position', parent=self)
        self.toolbar_end.setEnabled(False)
        self.toolbar_end.clicked.connect(self.clipEnd)
        self.toolbar_save = VCToolBarButton('Save Media', 'Save clips to a new media file', parent=self)
        self.toolbar_save.setObjectName('savebutton')
        self.toolbar_save.setEnabled(False)
        self.toolbar_save.clicked.connect(self.saveMedia)

        toolbarLayout = QHBoxLayout()
        toolbarLayout.setContentsMargins(0, 0, 0, 0)
        toolbarLayout.addStretch(1)
        toolbarLayout.addWidget(self.toolbar_open)
        toolbarLayout.addStretch(1)
        toolbarLayout.addWidget(self.toolbar_play)
        toolbarLayout.addStretch(1)
        toolbarLayout.addWidget(self.toolbar_start)
        toolbarLayout.addStretch(1)
        toolbarLayout.addWidget(self.toolbar_end)
        toolbarLayout.addStretch(1)
        toolbarLayout.addWidget(self.toolbar_save)
        toolbarLayout.addStretch(1)

        self.toolbarGroup = QGroupBox()
        self.toolbarGroup.setLayout(toolbarLayout)
        self.toolbarGroup.setStyleSheet('QGroupBox { border: 0; }')

        self.setToolBarStyle(self.settings.value('toolbarLabels', 'beside', type=str))

        togglesLayout = QHBoxLayout()
        togglesLayout.setSpacing(0)
        togglesLayout.setContentsMargins(0, 0, 0, 0)
        togglesLayout.addWidget(self.consoleButton)
        togglesLayout.addWidget(self.osdButton)
        togglesLayout.addWidget(self.thumbnailsButton)
        togglesLayout.addWidget(self.chaptersButton)
        togglesLayout.addWidget(self.smartcutButton)
        togglesLayout.addStretch(1)

        settingsLayout = QHBoxLayout()
        settingsLayout.setSpacing(0)
        settingsLayout.setContentsMargins(0, 0, 0, 0)
        settingsLayout.addWidget(self.settingsButton)
        settingsLayout.addSpacing(5)
        settingsLayout.addWidget(self.streamsButton)
        settingsLayout.addSpacing(5)
        settingsLayout.addWidget(self.mediainfoButton)
        settingsLayout.addSpacing(5)
        settingsLayout.addWidget(self.menuButton)

        groupLayout = QVBoxLayout()
        groupLayout.addLayout(audioLayout)
        groupLayout.addSpacing(10)
        groupLayout.addLayout(settingsLayout)

        controlsLayout = QHBoxLayout()
        if sys.platform != 'darwin':
            controlsLayout.setContentsMargins(0, 0, 0, 0)
            controlsLayout.addSpacing(5)
        else:
            controlsLayout.setContentsMargins(10, 10, 10, 0)
        controlsLayout.addLayout(togglesLayout)
        controlsLayout.addSpacing(20)
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.toolbarGroup)
        controlsLayout.addStretch(1)
        controlsLayout.addSpacing(20)
        controlsLayout.addLayout(groupLayout)
        if sys.platform != 'darwin':
            controlsLayout.addSpacing(5)

        layout = QVBoxLayout()  
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 0)
        layout.addLayout(self.videoLayout)
        layout.addWidget(self.sliderWidget)
        layout.addSpacing(5)
        layout.addLayout(controlsLayout)

        self.setLayout(layout)
        self.seekSlider.initStyle()

    @pyqtSlot()
    def showAppMenu(self) -> None:
        pos = self.menuButton.mapToGlobal(self.menuButton.rect().topLeft())
        pos.setX(pos.x() - self.appmenu.sizeHint().width() + 30)
        pos.setY(pos.y() - 28)
        self.appmenu.popup(pos, self.quitAction)

    def initTheme(self) -> None:
        qApp.setStyle(VideoStyleDark() if self.theme == 'dark' else VideoStyleLight())
        self.fonts = [
            QFontDatabase.addApplicationFont(':/fonts/FuturaLT.ttf'),
            QFontDatabase.addApplicationFont(':/fonts/NotoSans-Bold.ttf'),
            QFontDatabase.addApplicationFont(':/fonts/NotoSans-Regular.ttf')
        ]
        self.style().loadQSS(self.theme)
        QApplication.setFont(QFont('Noto Sans', 12 if sys.platform == 'darwin' else 10, 300))

    def getMPV(self, parent: QWidget=None, file: str=None, start: float=0, pause: bool=True, mute: bool=False,
               volume: int=None) -> mpvWidget:
        widget = mpvWidget(
            parent=parent,
            file=file,
            #vo='opengl-cb',
            pause=pause,
            start=start,
            mute=mute,
            keep_open='always',
            idle=True,
            osd_font=self._osdfont,
            osd_level=0,
            osd_align_x='left',
            osd_align_y='top',
            cursor_autohide=False,
            input_cursor=False,
            input_default_bindings=False,
            stop_playback_on_init_failure=False,
            input_vo_keyboard=False,
            sub_auto=False,
            sid=False,
            video_sync='display-vdrop',
            audio_file_auto=False,
            quiet=True,
            volume=volume if volume is not None else self.parent.startupvol,
            opengl_pbo=self.enablePBO,
            keepaspect=self.keepRatio,
            hwdec=('auto' if self.hardwareDecoding else 'no'))
        widget.durationChanged.connect(self.on_durationChanged)
        widget.positionChanged.connect(self.on_positionChanged)
        return widget

    def _initNoVideo(self) -> None:
        self.novideoWidget = QWidget(self)
        self.novideoWidget.setObjectName('novideoWidget')
        self.novideoWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        openmediaLabel = VCBlinkText('open media to begin', self)
        openmediaLabel.setAlignment(Qt.AlignHCenter)
        _version = 'v{}'.format(qApp.applicationVersion())
        if self.parent.flatpak:
            _version += ' <font size="-1">- FLATPAK</font>'
        versionLabel = QLabel(_version, self)
        versionLabel.setObjectName('novideoversion')
        versionLabel.setAlignment(Qt.AlignRight)
        versionLayout = QHBoxLayout()
        versionLayout.setSpacing(0)
        versionLayout.setContentsMargins(0, 0, 10, 8)
        versionLayout.addWidget(versionLabel)
        novideoLayout = QVBoxLayout(self.novideoWidget)
        novideoLayout.setSpacing(0)
        novideoLayout.setContentsMargins(0, 0, 0, 0)
        novideoLayout.addStretch(20)
        novideoLayout.addWidget(openmediaLabel)
        novideoLayout.addStretch(1)
        novideoLayout.addLayout(versionLayout)

    def _initIcons(self) -> None:
        self.appIcon = qApp.windowIcon()
        self.muteIcon = QIcon(':/images/{}/muted.png'.format(self.theme))
        self.unmuteIcon = QIcon(':/images/{}/unmuted.png'.format(self.theme))
        self.chapterIcon = QIcon(':/images/chapters.png')
        self.upIcon = QIcon(':/images/up.png')
        self.downIcon = QIcon(':/images/down.png')
        self.removeIcon = QIcon(':/images/remove.png')
        self.removeAllIcon = QIcon(':/images/remove-all.png')
        self.openProjectIcon = QIcon(':/images/open.png')
        self.saveProjectIcon = QIcon(':/images/save.png')
        self.filtersIcon = QIcon(':/images/filters.png')
        self.mediaInfoIcon = QIcon(':/images/info.png')
        self.streamsIcon = QIcon(':/images/streams.png')
        self.changelogIcon = QIcon(':/images/changelog.png')
        self.viewLogsIcon = QIcon(':/images/viewlogs.png')
        self.updateCheckIcon = QIcon(':/images/update.png')
        self.keyRefIcon = QIcon(':/images/keymap.png')
        self.fullscreenIcon = QIcon(':/images/{}/fullscreen.png'.format(self.theme))
        self.settingsIcon = QIcon(':/images/settings.png')
        self.quitIcon = QIcon(':/images/quit.png')

    # noinspection PyArgumentList
    def _initActions(self) -> None:
        self.moveItemUpAction = QAction(self.upIcon, 'Move clip up', self, statusTip='Move clip position up in list',
                                        triggered=self.moveItemUp, enabled=False)
        self.moveItemDownAction = QAction(self.downIcon, 'Move clip down', self, triggered=self.moveItemDown,
                                          statusTip='Move clip position down in list', enabled=False)
        self.removeItemAction = QAction(self.removeIcon, 'Remove selected clip', self, triggered=self.removeItem,
                                        statusTip='Remove selected clip from list', enabled=False)
        self.removeAllAction = QAction(self.removeAllIcon, 'Remove all clips', self, triggered=self.clearList,
                                       statusTip='Remove all clips from list', enabled=False)
        self.editChapterAction = QAction(self.chapterIcon, 'Edit chapter name', self, triggered=self.editChapter,
                                         statusTip='Edit the selected chapter name', enabled=False)
        self.streamsAction = QAction(self.streamsIcon, 'Media streams', self, triggered=self.selectStreams,
                                     statusTip='Select the media streams to be included', enabled=False)
        self.mediainfoAction = QAction(self.mediaInfoIcon, 'Media information', self, triggered=self.mediaInfo,
                                       statusTip='View technical details about current media', enabled=False)
        self.openProjectAction = QAction(self.openProjectIcon, 'Open project file', self, triggered=self.openProject,
                                         statusTip='Open a previously saved project file (*.vcp or *.edl)',
                                         enabled=True)
        self.saveProjectAction = QAction(self.saveProjectIcon, 'Save project file', self, triggered=self.saveProject,
                                         statusTip='Save current work to a project file (*.vcp or *.edl)',
                                         enabled=False)
        self.changelogAction = QAction(self.changelogIcon, 'View changelog', self, triggered=self.viewChangelog,
                                       statusTip='View log of changes')
        self.viewLogsAction = QAction(self.viewLogsIcon, 'View log file', self, triggered=VideoCutter.viewLogs,
                                      statusTip='View the application\'s log file')
        self.updateCheckAction = QAction(self.updateCheckIcon, 'Check for updates...', self,
                                         statusTip='Check for application updates', triggered=self.updater.check)
        self.aboutQtAction = QAction('About Qt', self, triggered=qApp.aboutQt, statusTip='About Qt')
        self.aboutAction = QAction('About {}'.format(qApp.applicationName()), self, triggered=self.aboutApp,
                                   statusTip='About {}'.format(qApp.applicationName()))
        self.keyRefAction = QAction(self.keyRefIcon, 'Keyboard shortcuts', self, triggered=self.showKeyRef,
                                    statusTip='View shortcut key bindings')
        self.settingsAction = QAction(self.settingsIcon, 'Settings', self, triggered=self.showSettings,
                                      statusTip='Configure application settings')
        self.fullscreenAction = QAction(self.fullscreenIcon, 'Toggle fullscreen', self, triggered=self.toggleFullscreen,
                                        statusTip='Toggle fullscreen display mode', enabled=False)
        self.quitAction = QAction(self.quitIcon, 'Quit', self, triggered=self.parent.close,
                                  statusTip='Quit the application')

    @property
    def _filtersMenu(self) -> QMenu:
        menu = QMenu('Video filters', self)
        self.blackdetectAction = VCFilterMenuAction(QPixmap(':/images/blackdetect.png'), 'BLACKDETECT',
                                                    'Create clips via black frame detection',
                                                    'Useful for skipping commercials or detecting scene transitions',
                                                    self)
        if sys.platform == 'darwin':
            self.blackdetectAction.triggered.connect(lambda: self.configFilters(VideoFilter.BLACKDETECT),
                                                     Qt.QueuedConnection)
        else:
            self.blackdetectAction.triggered.connect(lambda: self.configFilters(VideoFilter.BLACKDETECT),
                                                     Qt.DirectConnection)
        self.blackdetectAction.setEnabled(False)
        menu.setIcon(self.filtersIcon)
        menu.addAction(self.blackdetectAction)
        return menu

    def _initMenus(self) -> None:
        self.appmenu.addAction(self.openProjectAction)
        self.appmenu.addAction(self.saveProjectAction)
        self.appmenu.addSeparator()
        self.appmenu.addMenu(self._filtersMenu)
        self.appmenu.addSeparator()
        self.appmenu.addAction(self.fullscreenAction)
        self.appmenu.addAction(self.streamsAction)
        self.appmenu.addAction(self.mediainfoAction)
        self.appmenu.addAction(self.keyRefAction)
        self.appmenu.addSeparator()
        self.appmenu.addAction(self.settingsAction)
        self.appmenu.addSeparator()
        self.appmenu.addAction(self.viewLogsAction)
        self.appmenu.addAction(self.updateCheckAction)
        self.appmenu.addSeparator()
        self.appmenu.addAction(self.changelogAction)
        self.appmenu.addAction(self.aboutQtAction)
        self.appmenu.addAction(self.aboutAction)
        self.appmenu.addSeparator()
        self.appmenu.addAction(self.quitAction)

        self.clipindex_contextmenu.addAction(self.editChapterAction)
        self.clipindex_contextmenu.addSeparator()
        self.clipindex_contextmenu.addAction(self.moveItemUpAction)
        self.clipindex_contextmenu.addAction(self.moveItemDownAction)
        self.clipindex_contextmenu.addSeparator()
        self.clipindex_contextmenu.addAction(self.removeItemAction)
        self.clipindex_contextmenu.addAction(self.removeAllAction)

        self.clipindex_removemenu.addActions([self.removeItemAction, self.removeAllAction])
        self.clipindex_removemenu.aboutToShow.connect(self.initRemoveMenu)

        if sys.platform in {'win32', 'darwin'}:
            self.appmenu.setStyle(QStyleFactory.create('Fusion'))
            self.clipindex_contextmenu.setStyle(QStyleFactory.create('Fusion'))
            self.clipindex_removemenu.setStyle(QStyleFactory.create('Fusion'))

    def _initClipIndexHeader(self) -> None:
        if self.indexLayout == 'left':
            self.listHeaderButtonL.setVisible(False)
            self.listHeaderButtonR.setVisible(True)
        else:
            self.listHeaderButtonL.setVisible(True)
            self.listHeaderButtonR.setVisible(False)

    @pyqtSlot()
    def setClipIndexLayout(self) -> None:
        self.indexLayout = 'left' if self.indexLayout == 'right' else 'right'
        self.settings.setValue('indexLayout', self.indexLayout)
        left = self.videoLayout.takeAt(0)
        spacer = self.videoLayout.takeAt(0)
        right = self.videoLayout.takeAt(0)
        if isinstance(left, QVBoxLayout):
            if self.indexLayout == 'left':
                self.videoLayout.addItem(left)
                self.videoLayout.addItem(spacer)
                self.videoLayout.addItem(right)
            else:
                self.videoLayout.addItem(right)
                self.videoLayout.addItem(spacer)
                self.videoLayout.addItem(left)
        else:
            if self.indexLayout == 'left':
                self.videoLayout.addItem(right)
                self.videoLayout.addItem(spacer)
                self.videoLayout.addItem(left)
            else:
                self.videoLayout.addItem(left)
                self.videoLayout.addItem(spacer)
                self.videoLayout.addItem(right)
        self._initClipIndexHeader()

    def setToolBarStyle(self, labelstyle: str = 'beside') -> None:
        buttonlist = self.toolbarGroup.findChildren(VCToolBarButton)
        [button.setLabelStyle(labelstyle) for button in buttonlist]

    def setRunningTime(self, runtime: str) -> None:
        self.runtimeLabel.setText('<div align="right">{}</div>'.format(runtime))
        self.runtimeLabel.setToolTip('total runtime: {}'.format(runtime))
        self.runtimeLabel.setStatusTip('total running time: {}'.format(runtime))

    def getFileDialogOptions(self) -> QFileDialog.Options:
        options = QFileDialog.HideNameFilterDetails
        if not self.nativeDialogs:
            options |= QFileDialog.DontUseNativeDialog
        # noinspection PyTypeChecker
        return options

    @pyqtSlot()
    def showSettings(self):
        settingsDialog = SettingsDialog(self.videoService, self)
        settingsDialog.exec_()

    @pyqtSlot()
    def initRemoveMenu(self):
        self.removeItemAction.setEnabled(False)
        self.removeAllAction.setEnabled(False)
        if self.cliplist.count():
            self.removeAllAction.setEnabled(True)
            if len(self.cliplist.selectedItems()):
                self.removeItemAction.setEnabled(True)

    def itemMenu(self, pos: QPoint) -> None:
        globalPos = self.cliplist.mapToGlobal(pos)
        self.editChapterAction.setEnabled(False)
        self.moveItemUpAction.setEnabled(False)
        self.moveItemDownAction.setEnabled(False)
        self.initRemoveMenu()
        index = self.cliplist.currentRow()
        if index != -1:
            if len(self.cliplist.selectedItems()):
                self.editChapterAction.setEnabled(self.createChapters)
            if not self.inCut:
                if index > 0:
                    self.moveItemUpAction.setEnabled(True)
                if index < self.cliplist.count() - 1:
                    self.moveItemDownAction.setEnabled(True)
        self.clipindex_contextmenu.exec_(globalPos)

    def editChapter(self) -> None:
        index = self.cliplist.currentRow()
        name = self.clipTimes[index][4]
        name = name if name is not None else 'Chapter {}'.format(index + 1)
        dialog = VCInputDialog(self, 'Edit chapter name', 'Chapter name:', name)
        dialog.accepted.connect(lambda: self.on_editChapter(index, dialog.input.text()))
        dialog.exec_()

    def on_editChapter(self, index: int, text: str) -> None:
        self.clipTimes[index][4] = text
        self.renderClipIndex()

    def moveItemUp(self) -> None:
        index = self.cliplist.currentRow()
        if index != -1:
            tmpItem = self.clipTimes[index]
            del self.clipTimes[index]
            self.clipTimes.insert(index - 1, tmpItem)
            self.showText('clip moved up')
            self.renderClipIndex()

    def moveItemDown(self) -> None:
        index = self.cliplist.currentRow()
        if index != -1:
            tmpItem = self.clipTimes[index]
            del self.clipTimes[index]
            self.clipTimes.insert(index + 1, tmpItem)
            self.showText('clip moved down')
            self.renderClipIndex()

    def removeItem(self) -> None:
        index = self.cliplist.currentRow()
        if self.mediaAvailable:
            if self.inCut and index == self.cliplist.count() - 1:
                self.inCut = False
                self.initMediaControls()
        elif len(self.clipTimes) == 0:
            self.initMediaControls(False)
        del self.clipTimes[index]
        self.cliplist.takeItem(index)
        self.showText('clip removed')
        self.renderClipIndex()

    def clearList(self) -> None:
        self.clipTimes.clear()
        self.cliplist.clear()
        self.showText('all clips cleared')
        if self.mediaAvailable:
            self.inCut = False
            self.initMediaControls(True)
        else:
            self.initMediaControls(False)
        self.renderClipIndex()

    def projectFilters(self, savedialog: bool = False) -> str:
        if savedialog:
            return 'VidCutter Project (*.vcp);;MPlayer EDL (*.edl)'
        elif self.mediaAvailable:
            return 'Project files (*.edl *.vcp);;VidCutter Project (*.vcp);;MPlayer EDL (*.edl);;All files (*)'
        else:
            return 'VidCutter Project (*.vcp);;All files (*)'

    @staticmethod
    def mediaFilters(initial: bool = False) -> str:
        filters = 'All media files (*.{})'.format(' *.'.join(VideoService.config.filters.get('all')))
        if initial:
            return filters
        filters += ';;{};;All files (*)'.format(';;'.join(VideoService.config.filters.get('types')))
        return filters

    def openMedia(self) -> Optional[Callable]:
        cancel, callback = self.saveWarning()
        if cancel:
            if callback is not None:
                return callback()
            else:
                return
        filename, _ = QFileDialog.getOpenFileName(
            parent=self.parent,
            caption='Open media file',
            filter=self.mediaFilters(),
            initialFilter=self.mediaFilters(True),
            directory=(self.lastFolder if os.path.exists(self.lastFolder) else QDir.homePath()),
            options=self.getFileDialogOptions())
        if filename is not None and len(filename.strip()):
            self.lastFolder = QFileInfo(filename).absolutePath()
            self.loadMedia(filename)

    # noinspection PyUnusedLocal
    def openProject(self, checked: bool = False, project_file: str = None) -> Optional[Callable]:
        cancel, callback = self.saveWarning()
        if cancel:
            if callback is not None:
                return callback()
            else:
                return
        initialFilter = 'Project files (*.edl *.vcp)' if self.mediaAvailable else 'VidCutter Project (*.vcp)'
        if project_file is None:
            project_file, _ = QFileDialog.getOpenFileName(
                parent=self.parent,
                caption='Open project file',
                filter=self.projectFilters(),
                initialFilter=initialFilter,
                directory=(self.lastFolder if os.path.exists(self.lastFolder) else QDir.homePath()),
                options=self.getFileDialogOptions())
        if project_file is not None and len(project_file.strip()):
            if project_file != os.path.join(QDir.tempPath(), self.parent.TEMP_PROJECT_FILE):
                self.lastFolder = QFileInfo(project_file).absolutePath()
            file = QFile(project_file)
            info = QFileInfo(file)
            project_type = info.suffix()
            if not file.open(QFile.ReadOnly | QFile.Text):
                QMessageBox.critical(self.parent, 'Open project file',
                                     'Cannot read project file {0}:\n\n{1}'.format(project_file, file.errorString()))
                return
            qApp.setOverrideCursor(Qt.WaitCursor)
            self.clipTimes.clear()
            linenum = 1
            while not file.atEnd():
                # noinspection PyUnresolvedReferences
                line = file.readLine().trimmed()
                if line.length() > 0:
                    try:
                        line = line.data().decode()
                    except UnicodeDecodeError:
                        qApp.restoreOverrideCursor()
                        self.logger.error('Invalid project file was selected', exc_info=True)
                        sys.stderr.write('Invalid project file was selected')
                        QMessageBox.critical(self.parent, 'Invalid project file',
                                             'Could not make sense of the selected project file. Try viewing it in a '
                                             'text editor to ensure it is valid and not corrupted.')
                        return
                    if project_type == 'vcp' and linenum == 1:
                        self.loadMedia(line)
                        time.sleep(1)
                    else:
                        mo = self.project_files[project_type].match(line)
                        if mo:
                            start, stop, _, chapter = mo.groups()
                            clip_start = self.delta2QTime(float(start))
                            clip_end = self.delta2QTime(float(stop))
                            clip_image = self.captureImage(self.currentMedia, clip_start)
                            if project_type == 'vcp' and self.createChapters and len(chapter):
                                chapter = chapter[1:len(chapter) - 1]
                                if not len(chapter):
                                    chapter = None
                            else:
                                chapter = None
                            self.clipTimes.append([clip_start, clip_end, clip_image, '', chapter])
                        else:
                            qApp.restoreOverrideCursor()
                            QMessageBox.critical(self.parent, 'Invalid project file',
                                                 'Invalid entry at line {0}:\n\n{1}'.format(linenum, line))
                            return
                linenum += 1
            self.toolbar_start.setEnabled(True)
            self.toolbar_end.setDisabled(True)
            self.seekSlider.setRestrictValue(0, False)
            self.blackdetectAction.setEnabled(True)
            self.inCut = False
            self.newproject = True
            QTimer.singleShot(2000, self.selectClip)
            qApp.restoreOverrideCursor()
            if project_file != os.path.join(QDir.tempPath(), self.parent.TEMP_PROJECT_FILE):
                self.showText('project loaded')

    def saveProject(self, reboot: bool = False) -> None:
        if self.currentMedia is None:
            return
        if self.hasExternals():
            h2color = '#C681D5' if self.theme == 'dark' else '#642C68'
            acolor = '#EA95FF' if self.theme == 'dark' else '#441D4E'
            nosavetext = '''
                <style>
                    h2 {{
                        color: {h2color};
                        font-family: "Futura LT", sans-serif;
                        font-weight: normal;
                    }}
                    a {{
                        color: {acolor};
                        text-decoration: none;
                        font-weight: bold;
                    }}
                </style>
                <table border="0" cellpadding="6" cellspacing="0" width="350">
                    <tr>
                        <td><h2>Cannot save your current project</h2></td>
                    </tr>
                    <tr>
                        <td>
                            <p>Cannot save project containing external media files. Remove
                            all media files you have externally added and try again.</p>
                        </td>
                    </tr>
                </table>'''.format(**locals())
            nosave = QMessageBox(QMessageBox.Critical, 'Cannot save project', nosavetext, parent=self.parent)
            nosave.setStandardButtons(QMessageBox.Ok)
            nosave.exec_()
            return
        project_file, _ = os.path.splitext(self.currentMedia)
        if reboot:
            project_save = os.path.join(QDir.tempPath(), self.parent.TEMP_PROJECT_FILE)
            ptype = 'VidCutter Project (*.vcp)'
        else:
            project_save, ptype = QFileDialog.getSaveFileName(
                parent=self.parent,
                caption='Save project',
                directory='{}.vcp'.format(project_file),
                filter=self.projectFilters(True),
                initialFilter='VidCutter Project (*.vcp)',
                options=self.getFileDialogOptions())
        if project_save is not None and len(project_save.strip()):
            file = QFile(project_save)
            if not file.open(QFile.WriteOnly | QFile.Text):
                QMessageBox.critical(self.parent, 'Cannot save project',
                                     'Cannot save project file at {0}:\n\n{1}'.format(project_save, file.errorString()))
                return
            qApp.setOverrideCursor(Qt.WaitCursor)
            if ptype == 'VidCutter Project (*.vcp)':
                # noinspection PyUnresolvedReferences
                QTextStream(file) << '{}\n'.format(self.currentMedia)
            for clip in self.clipTimes:
                start_time = timedelta(hours=clip[0].hour(), minutes=clip[0].minute(), seconds=clip[0].second(),
                                       milliseconds=clip[0].msec())
                stop_time = timedelta(hours=clip[1].hour(), minutes=clip[1].minute(), seconds=clip[1].second(),
                                      milliseconds=clip[1].msec())
                if ptype == 'VidCutter Project (*.vcp)':
                    if self.createChapters:
                        chapter = '"{}"'.format(clip[4]) if clip[4] is not None else '""'
                    else:
                        chapter = ''
                    # noinspection PyUnresolvedReferences
                    QTextStream(file) << '{0}\t{1}\t{2}\t{3}\n'.format(self.delta2String(start_time),
                                                                       self.delta2String(stop_time), 0, chapter)
                else:
                    # noinspection PyUnresolvedReferences
                    QTextStream(file) << '{0}\t{1}\t{2}\n'.format(self.delta2String(start_time),
                                                                  self.delta2String(stop_time), 0)
            qApp.restoreOverrideCursor()
            self.projectSaved = True
            if not reboot:
                self.showText('project file saved')

    def loadMedia(self, filename: str) -> None:
        if not os.path.isfile(filename):
            return
        self.currentMedia = filename
        self.initMediaControls(True)
        self.projectDirty, self.projectSaved = False, False
        self.cliplist.clear()
        self.clipTimes.clear()
        self.totalRuntime = 0
        self.setRunningTime(self.delta2QTime(self.totalRuntime).toString(self.runtimeformat))
        self.seekSlider.clearRegions()
        self.taskbar.init()
        self.parent.setWindowTitle('{0} - {1}'.format(qApp.applicationName(), os.path.basename(self.currentMedia)))
        if not self.mediaAvailable:
            self.videoLayout.replaceWidget(self.novideoWidget, self.videoplayerWidget)
            self.novideoWidget.hide()
            self.novideoWidget.deleteLater()
            self.videoplayerWidget.show()
            self.mediaAvailable = True
        try:
            self.videoService.setMedia(self.currentMedia)
            self.seekSlider.setFocus()
            self.mpvWidget.play(self.currentMedia)
        except InvalidMediaException:
            qApp.restoreOverrideCursor()
            self.initMediaControls(False)
            self.logger.error('Could not load media file', exc_info=True)
            QMessageBox.critical(self.parent, 'Could not load media file',
                                 '<h3>Invalid media file selected</h3><p>All attempts to make sense of the file have '
                                 'failed. Try viewing it in another media player and if it plays as expected please '
                                 'report it as a bug. Use the link in the About VidCutter menu option for details '
                                 'and make sure to include your operating system, video card, the invalid media file '
                                 'and the version of VidCutter you are currently using.</p>')

    def setPlayButton(self, playing: bool=False) -> None:
        self.toolbar_play.setup('{} Media'.format('Pause' if playing else 'Play'),
                                'Pause currently playing media' if playing else 'Play currently loaded media',
                                True)

    def playMedia(self) -> None:
        playstate = self.mpvWidget.property('pause')
        self.setPlayButton(playstate)
        self.taskbar.setState(playstate)
        self.timeCounter.clearFocus()
        self.frameCounter.clearFocus()
        self.mpvWidget.pause()

    def showText(self, text: str, duration: int = 3, override: bool = False) -> None:
        if self.mediaAvailable:
            if not self.osdButton.isChecked() and not override:
                return
            if len(text.strip()):
                self.mpvWidget.showText(text, duration)

    def initMediaControls(self, flag: bool = True) -> None:
        self.toolbar_play.setEnabled(flag)
        self.toolbar_start.setEnabled(flag)
        self.toolbar_end.setEnabled(False)
        self.toolbar_save.setEnabled(False)
        self.streamsAction.setEnabled(flag)
        self.streamsButton.setEnabled(flag)
        self.mediainfoAction.setEnabled(flag)
        self.mediainfoButton.setEnabled(flag)
        self.fullscreenButton.setEnabled(flag)
        self.fullscreenAction.setEnabled(flag)
        self.seekSlider.clearRegions()
        self.blackdetectAction.setEnabled(flag)
        if flag:
            self.seekSlider.setRestrictValue(0)
        else:
            self.seekSlider.setValue(0)
            self.seekSlider.setRange(0, 0)
            self.timeCounter.reset()
            self.frameCounter.reset()
        self.openProjectAction.setEnabled(flag)
        self.saveProjectAction.setEnabled(False)

    @pyqtSlot(int)
    def setPosition(self, position: int) -> None:
        if position >= self.seekSlider.restrictValue:
            self.mpvWidget.seek(position / 1000)

    @pyqtSlot(float, int)
    def on_positionChanged(self, progress: float, frame: int) -> None:
        progress *= 1000
        if self.seekSlider.restrictValue < progress or progress == 0:
            self.seekSlider.setValue(int(progress))
            self.timeCounter.setTime(self.delta2QTime(round(progress)).toString(self.timeformat))
            self.frameCounter.setFrame(frame)
            if self.seekSlider.maximum() > 0:
                self.taskbar.setProgress(float(progress / self.seekSlider.maximum()), True)

    @pyqtSlot(float, int)
    def on_durationChanged(self, duration: float, frames: int) -> None:
        duration *= 1000
        self.seekSlider.setRange(0, int(duration))
        self.timeCounter.setDuration(self.delta2QTime(round(duration)).toString(self.timeformat))
        self.frameCounter.setFrameCount(frames)

    @pyqtSlot()
    @pyqtSlot(QListWidgetItem)
    def selectClip(self, item: QListWidgetItem = None) -> None:
        # noinspection PyBroadException
        try:
            row = self.cliplist.row(item) if item is not None else 0
            if item is None:
                self.cliplist.item(row).setSelected(True)
            if not len(self.clipTimes[row][3]):
                self.seekSlider.selectRegion(row)
                self.setPosition(self.clipTimes[row][0].msecsSinceStartOfDay())
        except Exception:
            self.doPass()

    def muteAudio(self) -> None:
        if self.mpvWidget.property('mute'):
            self.showText('audio enabled')
            self.muteButton.setIcon(self.unmuteIcon)
            self.muteButton.setToolTip('Mute')
        else:
            self.showText('audio disabled')
            self.muteButton.setIcon(self.muteIcon)
            self.muteButton.setToolTip('Unmute')
        self.mpvWidget.mute()

    def setVolume(self, vol: int) -> None:
        self.settings.setValue('volume', vol)
        if self.mediaAvailable:
            self.mpvWidget.volume(vol)

    @pyqtSlot(bool)
    def toggleThumbs(self, checked: bool) -> None:
        self.seekSlider.showThumbs = checked
        self.saveSetting('timelineThumbs', checked)
        if checked:
            self.showText('thumbnails enabled')
            self.seekSlider.initStyle()
            if self.mediaAvailable:
                self.seekSlider.reloadThumbs()
        else:
            self.showText('thumbnails disabled')
            self.seekSlider.removeThumbs()
            self.seekSlider.initStyle()

    @pyqtSlot(bool)
    def toggleConsole(self, checked: bool) -> None:
        if not hasattr(self, 'debugonstart'):
            self.debugonstart = os.getenv('DEBUG', False)
        if checked:
            self.mpvWidget.setLogLevel('v')
            os.environ['DEBUG'] = '1'
            self.parent.console.show()
        else:
            if not self.debugonstart:
                os.environ['DEBUG'] = '0'
                self.mpvWidget.setLogLevel('error')
            self.parent.console.hide()
        self.saveSetting('showConsole', checked)

    @pyqtSlot(bool)
    def toggleChapters(self, checked: bool) -> None:
        self.createChapters = checked
        self.saveSetting('chapters', self.createChapters)
        self.chaptersButton.setChecked(self.createChapters)
        self.showText('chapters {}'.format('enabled' if checked else 'disabled'))
        if checked:
            exist = False
            for clip in self.clipTimes:
                if clip[4] is not None:
                    exist = True
                    break
            if exist:
                chapterswarn = VCMessageBox('Restore chapter names', 'Chapter names found in memory',
                                            'Would you like to restore previously set chapter names?',
                                            buttons=QMessageBox.Yes | QMessageBox.No, parent=self)
                if chapterswarn.exec_() == QMessageBox.No:
                    for clip in self.clipTimes:
                        clip[4] = None
        self.renderClipIndex()

    @pyqtSlot(bool)
    def toggleSmartCut(self, checked: bool) -> None:
        self.smartcut = checked
        self.saveSetting('smartcut', self.smartcut)
        self.smartcutButton.setChecked(self.smartcut)
        self.showText('SmartCut {}'.format('enabled' if checked else 'disabled'))

    @pyqtSlot(list)
    def addScenes(self, scenes: List[list]) -> None:
        if len(scenes):
            [
                self.clipTimes.append([scene[0], scene[1], self.captureImage(self.currentMedia, scene[0]), '', None])
                for scene in scenes if len(scene)
            ]
            self.renderClipIndex()
        self.filterProgressBar.done(VCProgressDialog.Accepted)

    @pyqtSlot(VideoFilter)
    def configFilters(self, name: VideoFilter) -> None:
        if name == VideoFilter.BLACKDETECT:
            desc = '<p>Detect video intervals that are (almost) completely black. Can be useful to detect chapter ' \
                   'transitions, commercials, or invalid recordings. You can set the minimum duration of ' \
                   'a detected black interval above to adjust the sensitivity.</p>' \
                   '<p><b>WARNING:</b> this can take a long time to complete depending on the length and quality ' \
                   'of the source media.</p>'
            d = VCDoubleInputDialog(self, 'BLACKDETECT - Filter settings', 'Minimum duration for black scenes:',
                                    self.filter_settings.blackdetect.default_duration,
                                    self.filter_settings.blackdetect.min_duration, 999.9, 1, 0.1, desc, 'secs')
            d.buttons.accepted.connect(
                lambda: self.startFilters('detecting scenes (press ESC to cancel)',
                                          partial(self.videoService.blackdetect, d.value), d))
            d.setFixedSize(435, d.sizeHint().height())
            d.exec_()

    @pyqtSlot(str, partial, QDialog)
    def startFilters(self, progress_text: str, filter_func: partial, config_dialog: QDialog) -> None:
        config_dialog.close()
        self.parent.lock_gui(True)
        self.filterProgress(progress_text)
        filter_func()

    @pyqtSlot()
    def stopFilters(self) -> None:
        self.videoService.killFilterProc()
        self.parent.lock_gui(False)

    def filterProgress(self, msg: str) -> None:
        self.filterProgressBar = VCProgressDialog(self, modal=False)
        self.filterProgressBar.finished.connect(self.stopFilters)
        self.filterProgressBar.setText(msg)
        self.filterProgressBar.setMinimumWidth(600)
        self.filterProgressBar.show()

    @pyqtSlot()
    def addExternalClips(self) -> None:
        clips, _ = QFileDialog.getOpenFileNames(
            parent=self.parent,
            caption='Add media files',
            filter=self.mediaFilters(),
            initialFilter=self.mediaFilters(True),
            directory=(self.lastFolder if os.path.exists(self.lastFolder) else QDir.homePath()),
            options=self.getFileDialogOptions())
        if clips is not None and len(clips):
            self.lastFolder = QFileInfo(clips[0]).absolutePath()
            filesadded = False
            cliperrors = list()
            for file in clips:
                if len(self.clipTimes) > 0:
                    lastItem = self.clipTimes[len(self.clipTimes) - 1]
                    file4Test = lastItem[3] if len(lastItem[3]) else self.currentMedia
                    if self.videoService.testJoin(file4Test, file):
                        self.clipTimes.append([QTime(0, 0), self.videoService.duration(file),
                                               self.captureImage(file, QTime(0, 0, second=2), True), file])
                        filesadded = True
                    else:
                        cliperrors.append((file,
                                           (self.videoService.lastError if len(self.videoService.lastError) else '')))
                        self.videoService.lastError = ''
                else:
                    self.clipTimes.append([QTime(0, 0), self.videoService.duration(file),
                                           self.captureImage(file, QTime(0, 0, second=2), True), file])
                    filesadded = True
            if len(cliperrors):
                detailedmsg = '''<p>The file(s) listed were found to be incompatible for inclusion to the clip index as
                            they failed to join in simple tests used to ensure their compatibility. This is
                            commonly due to differences in frame size, audio/video formats (codecs), or both.</p>
                            <p>You can join these files as they currently are using traditional video editors like
                            OpenShot, Kdenlive, ShotCut, Final Cut Pro or Adobe Premiere. They can re-encode media
                            files with mixed properties so that they are then matching and able to be joined but
                            be aware that this can be a time consuming process and almost always results in
                            degraded video quality.</p>
                            <p>Re-encoding video is not going to ever be supported by VidCutter because those tools
                            are already available for you both free and commercially.</p>'''
                errordialog = ClipErrorsDialog(cliperrors, self)
                errordialog.setDetailedMessage(detailedmsg)
                errordialog.show()
            if filesadded:
                self.showText('media added to index')
                self.renderClipIndex()

    def hasExternals(self) -> bool:
        return True in [len(item[3]) > 0 for item in self.clipTimes]

    def clipStart(self) -> None:
        starttime = self.delta2QTime(self.seekSlider.value())
        self.clipTimes.append([starttime, '', self.captureImage(self.currentMedia, starttime), '', None])
        self.timeCounter.setMinimum(starttime.toString(self.timeformat))
        self.frameCounter.lockMinimum()
        self.toolbar_start.setDisabled(True)
        self.toolbar_end.setEnabled(True)
        self.clipindex_add.setDisabled(True)
        self.seekSlider.setRestrictValue(self.seekSlider.value(), True)
        self.blackdetectAction.setDisabled(True)
        self.inCut = True
        self.showText('clip started at {}'.format(starttime.toString(self.timeformat)))
        self.renderClipIndex()
        self.cliplist.scrollToBottom()

    def clipEnd(self) -> None:
        item = self.clipTimes[len(self.clipTimes) - 1]
        endtime = self.delta2QTime(self.seekSlider.value())
        if endtime.__lt__(item[0]):
            QMessageBox.critical(self.parent, 'Invalid END Time',
                                 'The clip end time must come AFTER it\'s start time. Please try again.')
            return
        item[1] = endtime
        self.toolbar_start.setEnabled(True)
        self.toolbar_end.setDisabled(True)
        self.clipindex_add.setEnabled(True)
        self.timeCounter.setMinimum()
        self.seekSlider.setRestrictValue(0, False)
        self.blackdetectAction.setEnabled(True)
        self.inCut = False
        self.showText('clip ends at {}'.format(endtime.toString(self.timeformat)))
        self.renderClipIndex()
        self.cliplist.scrollToBottom()

    @pyqtSlot()
    @pyqtSlot(bool)
    def setProjectDirty(self, dirty: bool=True) -> None:
        self.projectDirty = dirty

    # noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
    @pyqtSlot(QModelIndex, int, int, QModelIndex, int)
    def syncClipList(self, parent: QModelIndex, start: int, end: int, destination: QModelIndex, row: int) -> None:
        index = row - 1 if start < row else row
        clip = self.clipTimes.pop(start)
        self.clipTimes.insert(index, clip)
        if not len(clip[3]):
            self.seekSlider.switchRegions(start, index)
        self.showText('clip order updated')
        self.renderClipIndex()

    def renderClipIndex(self) -> None:
        self.seekSlider.clearRegions()
        self.totalRuntime = 0
        externals = self.cliplist.renderClips(self.clipTimes)
        if len(self.clipTimes) and not self.inCut and externals != 1:
            self.toolbar_save.setEnabled(True)
            self.saveProjectAction.setEnabled(True)
        if self.inCut or len(self.clipTimes) == 0 or not isinstance(self.clipTimes[0][1], QTime):
            self.toolbar_save.setEnabled(False)
            self.saveProjectAction.setEnabled(False)
        self.setRunningTime(self.delta2QTime(self.totalRuntime).toString(self.runtimeformat))

    @staticmethod
    def delta2QTime(msecs: Union[float, int]) -> QTime:
        if isinstance(msecs, float):
            msecs = round(msecs * 1000)
        t = QTime(0, 0)
        return t.addMSecs(msecs)

    @staticmethod
    def qtime2delta(qtime: QTime) -> float:
        return timedelta(hours=qtime.hour(), minutes=qtime.minute(), seconds=qtime.second(),
                         milliseconds=qtime.msec()).total_seconds()

    @staticmethod
    def delta2String(td: timedelta) -> str:
        if td is None or td == timedelta.max:
            return ''
        else:
            return '%f' % (td.days * 86400 + td.seconds + td.microseconds / 1000000.)

    def captureImage(self, source: str, frametime: QTime, external: bool = False) -> QPixmap:
        return VideoService.captureFrame(self.settings, source, frametime.toString(self.timeformat), external=external)

    def saveMedia(self) -> None:
        clips = len(self.clipTimes)
        source_file, source_ext = os.path.splitext(self.currentMedia if self.currentMedia is not None
                                                   else self.clipTimes[0][3])
        suggestedFilename = '{0}_EDIT{1}'.format(source_file, source_ext)
        filefilter = 'Video files (*{0})'.format(source_ext)
        if clips > 0:
            self.finalFilename, _ = QFileDialog.getSaveFileName(
                parent=self.parent,
                caption='Save media file',
                directory=suggestedFilename,
                filter=filefilter,
                options=self.getFileDialogOptions())
            if self.finalFilename is None or not len(self.finalFilename.strip()):
                return
            file, ext = os.path.splitext(self.finalFilename)
            if len(ext) == 0 and len(source_ext):
                self.finalFilename += source_ext
            self.lastFolder = QFileInfo(self.finalFilename).absolutePath()
            self.toolbar_save.setDisabled(True)
            if not os.path.isdir(self.workFolder):
                os.mkdir(self.workFolder)
            if self.smartcut:
                self.seekSlider.showProgress(6 if clips > 1 else 5)
                self.parent.lock_gui(True)
                self.videoService.smartinit(clips)
                self.smartcutter(file, source_file, source_ext)
                return
            steps = 3 if clips > 1 else 2
            self.seekSlider.showProgress(steps)
            self.parent.lock_gui(True)
            filename, filelist = '', []
            for index, clip in enumerate(self.clipTimes):
                self.seekSlider.updateProgress(index)
                if len(clip[3]):
                    filelist.append(clip[3])
                else:
                    duration = self.delta2QTime(clip[0].msecsTo(clip[1])).toString(self.timeformat)
                    filename = '{0}_{1}{2}'.format(file, '{0:0>2}'.format(index), source_ext)
                    if not self.keepClips:
                        filename = os.path.join(self.workFolder, os.path.basename(filename))
                    filename = QDir.toNativeSeparators(filename)
                    filelist.append(filename)
                    if not self.videoService.cut(source='{0}{1}'.format(source_file, source_ext),
                                                 output=filename,
                                                 frametime=clip[0].toString(self.timeformat),
                                                 duration=duration,
                                                 allstreams=True):
                        self.completeOnError('<p>Failed to cut media file, assuming media is invalid or corrupt. '
                                             'Attempts are made to work around problematic media files, even '
                                             'when keyframes are incorrectly set or missing.</p><p>If you feel this '
                                             'is a bug in the software then please take the time to report it '
                                             'at our <a href="{}">GitHub Issues page</a> so that it can be fixed.</p>'
                                             .format(vidcutter.__bugreport__))
                        return
            self.joinMedia(filelist)

    def smartcutter(self, file: str, source_file: str, source_ext: str) -> None:
        self.smartcut_monitor = Munch(clips=[], results=[], externals=0)
        for index, clip in enumerate(self.clipTimes):
            if len(clip[3]):
                self.smartcut_monitor.clips.append(clip[3])
                self.smartcut_monitor.externals += 1
                if index == len(self.clipTimes):
                    self.smartmonitor()
            else:
                filename = '{0}_{1}{2}'.format(file, '{0:0>2}'.format(index), source_ext)
                if not self.keepClips:
                    filename = os.path.join(self.workFolder, os.path.basename(filename))
                filename = QDir.toNativeSeparators(filename)
                self.smartcut_monitor.clips.append(filename)
                self.videoService.smartcut(index=index,
                                           source='{0}{1}'.format(source_file, source_ext),
                                           output=filename,
                                           start=VideoCutter.qtime2delta(clip[0]),
                                           end=VideoCutter.qtime2delta(clip[1]),
                                           allstreams=True)

    @pyqtSlot(bool, str)
    def smartmonitor(self, success: bool = None, outputfile: str = None) -> None:
        if success is not None:
            if not success:
                self.logger.error('SmartCut failed for {}'.format(outputfile))
            self.smartcut_monitor.results.append(success)
        if len(self.smartcut_monitor.results) == len(self.smartcut_monitor.clips) - self.smartcut_monitor.externals:
            if False not in self.smartcut_monitor.results:
                self.joinMedia(self.smartcut_monitor.clips)

    def joinMedia(self, filelist: list) -> None:
        if len(filelist) > 1:
            self.seekSlider.updateProgress()
            rc = False
            chapters = None
            if self.createChapters:
                chapters = []
                [
                    chapters.append(clip[4] if clip[4] is not None else 'Chapter {}'.format(index + 1))
                    for index, clip in enumerate(self.clipTimes)
                ]
            if self.videoService.isMPEGcodec(filelist[0]):
                self.logger.info('source file is MPEG based so join via MPEG-TS')
                rc = self.videoService.mpegtsJoin(filelist, self.finalFilename, chapters)
            if not rc or QFile(self.finalFilename).size() < 1000:
                self.logger.info('MPEG-TS based join failed, will retry using standard concat')
                rc = self.videoService.join(filelist, self.finalFilename, True, chapters)
            if not rc or QFile(self.finalFilename).size() < 1000:
                self.logger.info('join resulted in 0 length file, trying again without all stream mapping')
                self.videoService.join(filelist, self.finalFilename, False, chapters)
            if not self.keepClips:
                for f in filelist:
                    clip = self.clipTimes[filelist.index(f)]
                    if not len(clip[3]) and os.path.isfile(f):
                        QFile.remove(f)
            self.complete(False)
        else:
            self.complete(True, filelist[-1])

    def complete(self, rename: bool=True, filename: str=None) -> None:
        if rename and filename is not None:
            # noinspection PyCallByClass
            QFile.remove(self.finalFilename)
            # noinspection PyCallByClass
            QFile.rename(filename, self.finalFilename)
        self.videoService.finalize(self.finalFilename)
        self.seekSlider.updateProgress()
        self.toolbar_save.setEnabled(True)
        self.parent.lock_gui(False)
        self.notify = JobCompleteNotification(
            self.finalFilename,
            self.sizeof_fmt(int(QFileInfo(self.finalFilename).size())),
            self.delta2QTime(self.totalRuntime).toString(self.runtimeformat),
            self.getAppIcon(encoded=True),
            self)
        self.notify.closed.connect(self.seekSlider.clearProgress)
        self.notify.show()
        if self.smartcut:
            QTimer.singleShot(1000, self.cleanup)
        self.setProjectDirty(False)

    @pyqtSlot(str)
    def completeOnError(self, errormsg: str) -> None:
        if self.smartcut:
            self.videoService.smartabort()
            QTimer.singleShot(1500, self.cleanup)
        self.parent.lock_gui(False)
        self.seekSlider.clearProgress()
        self.toolbar_save.setEnabled(True)
        self.parent.errorHandler(errormsg)

    def cleanup(self) -> None:
        if hasattr(self.videoService, 'smartcut_jobs'):
            delattr(self.videoService, 'smartcut_jobs')
        if hasattr(self, 'smartcut_monitor'):
            delattr(self, 'smartcut_monitor')
        self.videoService.smartcutError = False

    def saveSetting(self, setting: str, checked: bool) -> None:
        self.settings.setValue(setting, 'on' if checked else 'off')

    @pyqtSlot()
    def mediaInfo(self) -> None:
        if self.mediaAvailable:
            if self.videoService.backends.mediainfo is None:
                self.logger.error('mediainfo could not be found on the system')
                QMessageBox.critical(self.parent, 'Missing mediainfo utility',
                                     'The <b>mediainfo</b> command could not be found on your system which '
                                     'is required for this feature to work.<br/><br/>Linux users can simply '
                                     'install the <b>mediainfo</b> package using the package manager you use to '
                                     'install software (e.g. apt, pacman, dnf, zypper, etc.)')
                return
            mediainfo = MediaInfo(media=self.currentMedia, parent=self)
            mediainfo.show()

    @pyqtSlot()
    def selectStreams(self) -> None:
        if self.mediaAvailable and self.videoService.streams:
            if self.hasExternals():
                nostreamstext = '''
                    <style>
                        h2 {{
                            color: {0};
                            font-family: "Futura LT", sans-serif;
                            font-weight: normal;
                        }}
                    </style>
                    <table border="0" cellpadding="6" cellspacing="0" width="350">
                        <tr>
                            <td><h2>Cannot configure stream selection</h2></td>
                        </tr>
                        <tr>
                            <td>
                                Stream selection cannot be configured when external media files
                                are added to your clip index. Remove all external files from your
                                clip index and try again.
                            </td>
                        </tr>
                    </table>'''.format('#C681D5' if self.theme == 'dark' else '#642C68')
                nostreams = QMessageBox(QMessageBox.Critical,
                                        'Stream selection is unavailable',
                                        nostreamstext,
                                        parent=self.parent)
                nostreams.setStandardButtons(QMessageBox.Ok)
                nostreams.exec_()
                return
            streamSelector = StreamSelector(self.videoService, self)
            streamSelector.show()

    def saveWarning(self) -> tuple:
        if self.mediaAvailable and self.projectDirty and not self.projectSaved:
            savewarn = VCMessageBox('Warning', 'Unsaved changes found in project',
                                    'Would you like to save your project?', parent=self)
            savebutton = savewarn.addButton('Save project', QMessageBox.YesRole)
            savewarn.addButton('Do not save', QMessageBox.NoRole)
            cancelbutton = savewarn.addButton('Cancel', QMessageBox.RejectRole)
            savewarn.exec_()
            res = savewarn.clickedButton()
            if res == savebutton:
                return True, self.saveProject
            elif res == cancelbutton:
                return True, None
        return False, None

    @pyqtSlot()
    def showKeyRef(self) -> None:
        msgtext = '<img src=":/images/{}/shortcuts.png" />'.format(self.theme)
        msgbox = QMessageBox(QMessageBox.NoIcon, 'Keyboard shortcuts', msgtext, QMessageBox.Ok, self,
                             Qt.Window | Qt.Dialog | Qt.WindowCloseButtonHint)
        msgbox.setObjectName('shortcuts')
        msgbox.setContentsMargins(10, 10, 10, 10)
        msgbox.setMinimumWidth(400 if self.parent.scale == 'LOW' else 600)
        msgbox.exec_()

    @pyqtSlot()
    def aboutApp(self) -> None:
        about = About(self.videoService, self.mpvWidget, self)
        about.exec_()

    @staticmethod
    def getAppIcon(encoded: bool=False):
        icon = QIcon.fromTheme(qApp.applicationName().lower(), QIcon(':/images/vidcutter-small.png'))
        if not encoded:
            return icon
        iconimg = icon.pixmap(82, 82).toImage()
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QBuffer.WriteOnly)
        iconimg.save(buffer, 'PNG')
        base64enc = str(data.toBase64().data(), 'latin1')
        icon = 'data:vidcutter.png;base64,{}'.format(base64enc)
        return icon

    @staticmethod
    def sizeof_fmt(num: float, suffix: chr='B') -> str:
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Y', suffix)

    @pyqtSlot()
    def viewChangelog(self) -> None:
        changelog = Changelog(self)
        changelog.exec_()

    @staticmethod
    @pyqtSlot()
    def viewLogs() -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(logging.getLoggerClass().root.handlers[0].baseFilename))

    @pyqtSlot()
    def toggleFullscreen(self) -> None:
        if self.mediaAvailable:
            pause = self.mpvWidget.property('pause')
            mute = self.mpvWidget.property('mute')
            vol = self.mpvWidget.property('volume')
            pos = self.seekSlider.value() / 1000
            if self.mpvWidget.originalParent is not None:
                self.mpvWidget.shutdown()
                sip.delete(self.mpvWidget)
                del self.mpvWidget
                self.mpvWidget = self.getMPV(parent=self, file=self.currentMedia, start=pos, pause=pause, mute=mute,
                                             volume=vol)
                self.videoplayerLayout.insertWidget(0, self.mpvWidget)
                self.mpvWidget.originalParent = None
                self.parent.show()
            elif self.mpvWidget.parentWidget() != 0:
                self.parent.hide()
                self.mpvWidget.shutdown()
                self.videoplayerLayout.removeWidget(self.mpvWidget)
                sip.delete(self.mpvWidget)
                del self.mpvWidget
                self.mpvWidget = self.getMPV(file=self.currentMedia, start=pos, pause=pause, mute=mute, volume=vol)
                self.mpvWidget.originalParent = self
                self.mpvWidget.setGeometry(qApp.desktop().screenGeometry(self))
                self.mpvWidget.showFullScreen()

    def toggleOSD(self, checked: bool) -> None:
        self.showText('on-screen display {}'.format('enabled' if checked else 'disabled'), override=True)
        self.saveSetting('enableOSD', checked)

    @property
    def _osdfont(self) -> str:
        fontdb = QFontDatabase()
        return 'DejaVu Sans' if 'DejaVu Sans' in fontdb.families(QFontDatabase.Latin) else 'Noto Sans'

    def doPass(self) -> None:
        pass

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.mediaAvailable:

            if event.key() == Qt.Key_Space:
                self.playMedia()
                return

            if event.key() == Qt.Key_Escape and self.isFullScreen():
                self.toggleFullscreen()
                return

            if event.key() == Qt.Key_F:
                self.toggleFullscreen()
                return

            if event.key() == Qt.Key_Home:
                self.setPosition(self.seekSlider.minimum())
                return

            if event.key() == Qt.Key_End:
                self.setPosition(self.seekSlider.maximum())
                return

            if event.key() == Qt.Key_Left:
                self.mpvWidget.frameBackStep()
                self.setPlayButton(False)
                return

            if event.key() == Qt.Key_Down:
                if qApp.queryKeyboardModifiers() == Qt.ShiftModifier:
                    self.mpvWidget.seek(-self.level2Seek, 'relative+exact')
                else:
                    self.mpvWidget.seek(-self.level1Seek, 'relative+exact')
                return

            if event.key() == Qt.Key_Right:
                self.mpvWidget.frameStep()
                self.setPlayButton(False)
                return

            if event.key() == Qt.Key_Up:
                if qApp.queryKeyboardModifiers() == Qt.ShiftModifier:
                    self.mpvWidget.seek(self.level2Seek, 'relative+exact')
                else:
                    self.mpvWidget.seek(self.level1Seek, 'relative+exact')
                return

            if event.key() in {Qt.Key_Return, Qt.Key_Enter} and \
                    (not self.timeCounter.hasFocus() and not self.frameCounter.hasFocus()):
                if self.toolbar_start.isEnabled():
                    self.clipStart()
                elif self.toolbar_end.isEnabled():
                    self.clipEnd()
                return

        super(VideoCutter, self).keyPressEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        if hasattr(self, 'filterProgressBar') and self.filterProgressBar.isVisible():
            self.filterProgressBar.update()
        super(VideoCutter, self).showEvent(event)
