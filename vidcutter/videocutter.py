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

import logging
import os
import re
import sys
import time
from datetime import timedelta
from typing import Union

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QBuffer, QByteArray, QDir, QFile, QFileInfo, QModelIndex, QPoint, QSize,
                          Qt, QTextStream, QTime, QTimer, QUrl)
from PyQt5.QtGui import QDesktopServices, QFont, QFontDatabase, QIcon, QKeyEvent, QMovie, QPixmap
from PyQt5.QtWidgets import (QAction, qApp, QApplication, QDialogButtonBox, QFileDialog, QFrame, QGroupBox, QHBoxLayout,
                             QLabel, QListWidgetItem, QMenu, QMessageBox, QPushButton, QSizePolicy, QStyleFactory,
                             QVBoxLayout, QWidget)

# noinspection PyUnresolvedReferences
from vidcutter import resources
from vidcutter.about import About
from vidcutter.libs.mpvwidget import mpvWidget
from vidcutter.libs.munch import Munch
from vidcutter.libs.notifications import JobCompleteNotification
from vidcutter.libs.videoconfig import InvalidMediaException
from vidcutter.libs.videoservice import VideoService
from vidcutter.libs.widgets import ClipErrorsDialog, FrameCounter, TimeCounter, VolumeSlider
from vidcutter.settings import SettingsDialog
from vidcutter.updater import Updater
from vidcutter.videoinfo import VideoInfo
from vidcutter.videolist import VideoList
from vidcutter.videoslider import VideoSlider
from vidcutter.videosliderwidget import VideoSliderWidget
from vidcutter.videostyle import VideoStyleDark, VideoStyleLight
from vidcutter.videotoolbar import VideoToolBar

if sys.platform.startswith('linux'):
    from vidcutter.libs.taskbarprogress import TaskbarProgress


class VideoCutter(QWidget):
    errorOccurred = pyqtSignal(str)

    timeformat = 'hh:mm:ss.zzz'
    runtimeformat = 'hh:mm:ss'

    def __init__(self, parent: QWidget):
        super(VideoCutter, self).__init__(parent)
        self.setObjectName('videocutter')
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        self.theme = self.parent.theme
        self.workFolder = self.parent.WORKING_FOLDER
        self.settings = self.parent.settings
        self.currentMedia, self.mediaAvailable, self.mpvError = None, False, False
        self.projectDirty, self.projectSaved = False, False
        self.initTheme()

        self.updater = Updater(self.parent)

        self.seekSlider = VideoSlider(self)
        self.seekSlider.sliderMoved.connect(self.setPosition)
        self.sliderWidget = VideoSliderWidget(self, self.seekSlider)
        self.sliderWidget.setLoader(True)

        self.videoService = VideoService(self)
        self.videoService.progress.connect(self.seekSlider.updateProgress)
        self.videoService.finished.connect(self.smartmonitor)
        self.videoService.error.connect(self.completeOnError)

        if sys.platform.startswith('linux'):
            self.taskbar = TaskbarProgress(self)

        self.latest_release_url = 'https://github.com/ozmartian/vidcutter/releases/latest'

        self.clipTimes = []
        self.inCut, self.newproject = False, False
        self.finalFilename = ''
        self.totalRuntime, self.frameRate = 0, 0
        self.notifyInterval = 1000

        self.enableOSD = self.settings.value('enableOSD', 'on', type=str) in {'on', 'true'}
        self.hardwareDecoding = self.settings.value('hwdec', 'on', type=str) in {'on', 'auto'}
        self.keepRatio = self.settings.value('aspectRatio', 'keep', type=str) == 'keep'
        self.keepClips = self.settings.value('keepClips', 'off', type=str) in {'on', 'true'}
        self.nativeDialogs = self.settings.value('nativeDialogs', 'on', type=str) in {'on', 'true'}
        self.timelineThumbs = self.settings.value('timelineThumbs', 'on', type=str) in {'on', 'true'}
        self.showConsole = self.settings.value('showConsole', 'off', type=str) in {'on', 'true'}
        self.smartcut = self.settings.value('smartcut', 'off', type=str) in {'on', 'true'}
        self.level1Seek = self.settings.value('level1Seek', 2, type=float)
        self.level2Seek = self.settings.value('level2Seek', 5, type=float)
        self.lastFolder = self.settings.value('lastFolder', QDir.homePath(), type=str)
        self.verboseLogs = self.parent.verboseLogs
        if not os.path.exists(self.lastFolder):
            self.lastFolder = QDir.homePath()

        self.edlblock_re = re.compile(r'(\d+(?:\.?\d+)?)\s(\d+(?:\.?\d+)?)\s([01])')

        self.initIcons()
        self.initActions()
        self.toolbar = VideoToolBar(self)
        self.initToolbar()

        self.appMenu, self.clipindex_removemenu, self.clipindex_contextmenu = QMenu(self), QMenu(self), QMenu(self)
        self.initMenus()

        self.initNoVideo()

        self.cliplist = VideoList(self)
        self.cliplist.customContextMenuRequested.connect(self.itemMenu)
        self.cliplist.itemClicked.connect(self.selectClip)
        self.cliplist.model().rowsInserted.connect(self.setProjectDirty)
        self.cliplist.model().rowsRemoved.connect(self.setProjectDirty)
        self.cliplist.model().rowsMoved.connect(self.setProjectDirty)
        self.cliplist.model().rowsMoved.connect(self.syncClipList)

        listHeader = QLabel(self)
        listHeader.setPixmap(QPixmap(':/images/{}/clipindex.png'.format(self.theme), 'PNG'))
        listHeader.setAlignment(Qt.AlignCenter)
        listHeader.setObjectName('listHeader')

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
        if sys.platform == 'win32':
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
        self.clipindexLayout.addWidget(listHeader)
        self.clipindexLayout.addWidget(self.cliplist)
        self.clipindexLayout.addWidget(self.runtimeLabel)
        self.clipindexLayout.addSpacing(3)
        self.clipindexLayout.addWidget(clipindexTools)

        self.videoLayout = QHBoxLayout()
        self.videoLayout.setContentsMargins(0, 0, 0, 0)
        self.videoLayout.addWidget(self.novideoWidget)
        self.videoLayout.addSpacing(10)
        self.videoLayout.addLayout(self.clipindexLayout)

        self.timeCounter = TimeCounter(self)
        self.timeCounter.timeChanged.connect(lambda newtime: self.setPosition(newtime.msecsSinceStartOfDay()))
        self.frameCounter = FrameCounter(self)
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

        self.mpvWidget = self.getMPV()
        self.mpvWidget.durationChanged.connect(self.on_durationChanged)
        self.mpvWidget.positionChanged.connect(self.on_positionChanged)

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
                                            toolTip='Toggle thumbnails', toggled=self.toggleThumbs)
        self.thumbnailsButton.setFixedSize(32, 29 if self.theme == 'dark' else 31)
        if self.timelineThumbs:
            self.thumbnailsButton.setChecked(True)
        else:
            self.seekSlider.setObjectName('nothumbs')

        # noinspection PyArgumentList
        self.osdButton = QPushButton(self, flat=True, checkable=True, objectName='osdButton', toolTip='Toggle OSD',
                                     statusTip='Toggle on-screen display', cursor=Qt.PointingHandCursor,
                                     toggled=self.toggleOSD)
        self.osdButton.setFixedSize(31, 29 if self.theme == 'dark' else 31)
        if self.enableOSD:
            self.osdButton.setChecked(True)

        if sys.platform == 'darwin':
            self.osdButton.setChecked(False)
            self.osdButton.hide()

        # noinspection PyArgumentList
        self.consoleButton = QPushButton(self, flat=True, checkable=True, objectName='consoleButton',
                                         statusTip='Toggle console window', toolTip='Toggle console',
                                         cursor=Qt.PointingHandCursor, toggled=self.toggleConsole)
        self.consoleButton.setFixedSize(31, 29 if self.theme == 'dark' else 31)
        if self.showConsole:
            self.consoleButton.setChecked(True)
            self.mpvWidget.setLogLevel('v')
            os.environ['DEBUG'] = '1'
            self.parent.console.show()

        # noinspection PyArgumentList
        self.smartcutButton = QPushButton(self, flat=True, checkable=True, objectName='smartcutButton',
                                          toolTip='Toggle SmartCut', statusTip='Toggle frame accurate cutting',
                                          cursor=Qt.PointingHandCursor, toggled=self.toggleSmartCut)
        self.smartcutButton.setFixedSize(32, 29 if self.theme == 'dark' else 31)
        if self.smartcut:
            self.smartcutButton.setChecked(True)

        # noinspection PyArgumentList
        self.muteButton = QPushButton(objectName='muteButton', icon=self.unmuteIcon, flat=True, toolTip='Mute',
                                      statusTip='Toggle audio mute', iconSize=QSize(16, 16), clicked=self.muteAudio,
                                      cursor=Qt.PointingHandCursor)

        # noinspection PyArgumentList
        self.volSlider = VolumeSlider(orientation=Qt.Horizontal, toolTip='Volume', statusTip='Adjust volume level',
                                      cursor=Qt.PointingHandCursor, value=self.parent.startupvol, minimum=0,
                                      maximum=130, sliderMoved=self.setVolume)

        self.volSlider.setMinimumHeight(22)
        if sys.platform == 'darwin':
            self.volSlider.setStyle(QStyleFactory.create('Macintosh'))

        # noinspection PyArgumentList
        self.fullscreenButton = QPushButton(objectName='fullscreenButton', icon=self.fullscreenIcon, flat=True,
                                            toolTip='Toggle fullscreen', statusTip='Switch to fullscreen video',
                                            iconSize=QSize(14, 14), clicked=self.toggleFullscreen,
                                            cursor=Qt.PointingHandCursor, enabled=False)

        # noinspection PyArgumentList
        self.settingsButton = QPushButton(self, toolTip='Settings', cursor=Qt.PointingHandCursor, flat=True,
                                          statusTip='Click to configure application settings',
                                          objectName='settingsButton', clicked=self.showSettings)
        self.settingsButton.setFixedSize(QSize(33, 32))

        # noinspection PyArgumentList
        self.mediainfoButton = QPushButton(self, toolTip='Media information', cursor=Qt.PointingHandCursor, flat=True,
                                           statusTip='Click to view technical information on currently loaded media',
                                           objectName='mediainfoButton', clicked=self.mediaInfo, enabled=False)
        self.mediainfoButton.setFixedSize(QSize(33, 32))

        # noinspection PyArgumentList
        self.menuButton = QPushButton(self, toolTip='Menu', cursor=Qt.PointingHandCursor, flat=True,
                                      objectName='menuButton', statusTip='Click to view menu options')
        self.menuButton.setFixedSize(QSize(33, 32))
        self.menuButton.setLayoutDirection(Qt.RightToLeft)
        self.menuButton.setMenu(self.appMenu)

        audioLayout = QHBoxLayout()
        audioLayout.setContentsMargins(0, 0, 0, 0)
        audioLayout.addWidget(self.muteButton)
        audioLayout.addSpacing(5)
        audioLayout.addWidget(self.volSlider)
        audioLayout.addSpacing(5)
        audioLayout.addWidget(self.fullscreenButton)

        toolbarLayout = QHBoxLayout()
        toolbarLayout.addWidget(self.toolbar)
        toolbarLayout.setContentsMargins(0, 0, 0, 0)

        toolbarGroup = QGroupBox()
        toolbarGroup.setLayout(toolbarLayout)
        toolbarGroup.setStyleSheet('border: 0;')

        togglesLayout = QHBoxLayout()
        togglesLayout.setSpacing(0)
        togglesLayout.setContentsMargins(0, 0, 0, 0)
        togglesLayout.addWidget(self.thumbnailsButton)
        togglesLayout.addWidget(self.osdButton)
        togglesLayout.addWidget(self.consoleButton)
        togglesLayout.addWidget(self.smartcutButton)
        togglesLayout.addStretch(1)

        settingsLayout = QHBoxLayout()
        settingsLayout.setSpacing(0)
        settingsLayout.setContentsMargins(0, 0, 0, 0)
        settingsLayout.addWidget(self.settingsButton)
        settingsLayout.addSpacing(5)
        settingsLayout.addWidget(self.mediainfoButton)
        settingsLayout.addSpacing(5)
        settingsLayout.addWidget(self.menuButton)

        groupLayout = QVBoxLayout()
        groupLayout.addLayout(audioLayout)
        groupLayout.addSpacing(10)
        groupLayout.addLayout(settingsLayout)

        controlsLayout = QHBoxLayout()
        controlsLayout.addSpacing(10)
        controlsLayout.addLayout(togglesLayout)
        controlsLayout.addSpacing(10)
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(toolbarGroup)
        controlsLayout.addStretch(1)
        controlsLayout.addSpacing(10)
        controlsLayout.addLayout(groupLayout)
        controlsLayout.addSpacing(10)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 0)
        layout.addLayout(self.videoLayout)
        layout.addWidget(self.sliderWidget)
        layout.addSpacing(5)
        layout.addLayout(controlsLayout)

        self.setLayout(layout)

        self.seekSlider.initStyle()

    def initTheme(self) -> None:
        qApp.setStyle(VideoStyleDark() if self.theme == 'dark' else VideoStyleLight())
        self.fonts = [
            QFontDatabase.addApplicationFont(':/fonts/FuturaLT.ttf'),
            QFontDatabase.addApplicationFont(':/fonts/NotoSans.ttc')
        ]
        self.style().loadQSS(self.theme, self.parent.devmode)
        QApplication.setFont(QFont('Noto Sans UI', 12 if sys.platform == 'darwin' else 10, 300))

    def getMPV(self, ) -> mpvWidget:
        return mpvWidget(
            parent=self,
            vo='opengl-cb',
            ytdl=False,
            pause=True,
            keep_open='always',
            idle=True,
            osc=False,
            osd_font='Noto Sans UI',
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
            # msg_level=('all=v' if self.verboseLogs else 'error'),
            volume=self.parent.startupvol,
            keepaspect=self.keepRatio,
            hwdec=('auto' if self.hardwareDecoding else 'no'))

    def initNoVideo(self) -> None:
        self.novideoWidget = QWidget(self)
        self.novideoWidget.setObjectName('novideoWidget')
        self.novideoWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.novideoLabel = QLabel(self)
        self.novideoLabel.setAlignment(Qt.AlignCenter)
        self.novideoMovie = QMovie(':/images/novideotext.gif', b'GIF', self)
        self.novideoMovie.setScaledSize(QSize(250, 30))
        self.novideoMovie.frameChanged.connect(lambda: self.novideoLabel.setPixmap(self.novideoMovie.currentPixmap()))
        self.novideoMovie.start()
        novideoLayout = QVBoxLayout()
        novideoLayout.addStretch(3)
        novideoLayout.addWidget(self.novideoLabel)
        novideoLayout.addStretch(1)
        self.novideoWidget.setLayout(novideoLayout)

    def initIcons(self) -> None:
        self.appIcon = qApp.windowIcon()
        self.openIcon = QIcon()
        self.openIcon.addFile(':/images/{}/toolbar-open.png'.format(self.theme), QSize(50, 53), QIcon.Normal)
        self.openIcon.addFile(':/images/%s/toolbar-open-on.png' % self.theme, QSize(50, 53), QIcon.Active)
        self.openIcon.addFile(':/images/%s/toolbar-open-disabled.png' % self.theme, QSize(50, 53), QIcon.Disabled)
        self.playIcon = QIcon()
        self.playIcon.addFile(':/images/%s/toolbar-play.png' % self.theme, QSize(50, 53), QIcon.Normal)
        self.playIcon.addFile(':/images/%s/toolbar-play-on.png' % self.theme, QSize(50, 53), QIcon.Active)
        self.playIcon.addFile(':/images/%s/toolbar-play-disabled.png' % self.theme, QSize(50, 53), QIcon.Disabled)
        self.pauseIcon = QIcon()
        self.pauseIcon.addFile(':/images/%s/toolbar-pause.png' % self.theme, QSize(50, 53), QIcon.Normal)
        self.pauseIcon.addFile(':/images/%s/toolbar-pause-on.png' % self.theme, QSize(50, 53), QIcon.Active)
        self.pauseIcon.addFile(':/images/%s/toolbar-pause-disabled.png' % self.theme, QSize(50, 53), QIcon.Disabled)
        self.cutStartIcon = QIcon()
        self.cutStartIcon.addFile(':/images/%s/toolbar-start.png' % self.theme, QSize(50, 53), QIcon.Normal)
        self.cutStartIcon.addFile(':/images/%s/toolbar-start-on.png' % self.theme, QSize(50, 53), QIcon.Active)
        self.cutStartIcon.addFile(':/images/%s/toolbar-start-disabled.png' % self.theme, QSize(50, 53), QIcon.Disabled)
        self.cutEndIcon = QIcon()
        self.cutEndIcon.addFile(':/images/%s/toolbar-end.png' % self.theme, QSize(50, 53), QIcon.Normal)
        self.cutEndIcon.addFile(':/images/%s/toolbar-end-on.png' % self.theme, QSize(50, 53), QIcon.Active)
        self.cutEndIcon.addFile(':/images/%s/toolbar-end-disabled.png' % self.theme, QSize(50, 53), QIcon.Disabled)
        self.saveIcon = QIcon()
        self.saveIcon.addFile(':/images/%s/toolbar-save.png' % self.theme, QSize(50, 53), QIcon.Normal)
        self.saveIcon.addFile(':/images/%s/toolbar-save-on.png' % self.theme, QSize(50, 53), QIcon.Active)
        self.saveIcon.addFile(':/images/%s/toolbar-save-disabled.png' % self.theme, QSize(50, 53), QIcon.Disabled)
        self.muteIcon = QIcon(':/images/{}/muted.png'.format(self.theme))
        self.unmuteIcon = QIcon(':/images/{}/unmuted.png'.format(self.theme))
        self.upIcon = QIcon(':/images/up.png')
        self.downIcon = QIcon(':/images/down.png')
        self.removeIcon = QIcon(':/images/remove.png')
        self.removeAllIcon = QIcon(':/images/remove-all.png')
        self.openProjectIcon = QIcon(':/images/open.png')
        self.saveProjectIcon = QIcon(':/images/save.png')
        self.mediaInfoIcon = QIcon(':/images/info.png')
        self.viewLogsIcon = QIcon(':/images/viewlogs.png')
        self.updateCheckIcon = QIcon(':/images/update.png')
        self.keyRefIcon = QIcon(':/images/keymap.png')
        self.fullscreenIcon = QIcon(':/images/{}/fullscreen.png'.format(self.theme))
        self.settingsIcon = QIcon(':/images/settings.png')
        self.quitIcon = QIcon(':/images/quit.png')

    # noinspection PyArgumentList
    def initActions(self) -> None:
        self.openAction = QAction(self.openIcon, 'Open\nMedia', self, statusTip='Open a media file for a cut & join',
                                  triggered=self.openMedia)
        self.playAction = QAction(self.playIcon, 'Play\nMedia', self, triggered=self.playMedia,
                                  statusTip='Play media file', enabled=False)
        self.pauseAction = QAction(self.pauseIcon, 'Pause\nMedia', self, visible=False, triggered=self.playMedia,
                                   statusTip='Pause currently playing media')
        self.cutStartAction = QAction(self.cutStartIcon, 'Start\nClip', self, triggered=self.clipStart, enabled=False,
                                      statusTip='Set the start position of a new clip')
        self.cutEndAction = QAction(self.cutEndIcon, 'End\nClip', self, triggered=self.clipEnd,
                                    enabled=False, statusTip='Set the end position of a new clip')
        self.saveAction = QAction(self.saveIcon, 'Save\nMedia', self, triggered=self.saveMedia, enabled=False,
                                  statusTip='Save clips to a new media file')
        self.moveItemUpAction = QAction(self.upIcon, 'Move up', self, statusTip='Move clip position up in list',
                                        triggered=self.moveItemUp, enabled=False)
        self.moveItemDownAction = QAction(self.downIcon, 'Move down', self, statusTip='Move clip position down in list',
                                          triggered=self.moveItemDown, enabled=False)
        self.removeItemAction = QAction(self.removeIcon, 'Remove selected', self, triggered=self.removeItem,
                                        statusTip='Remove selected clip from list', enabled=False)
        self.removeAllAction = QAction(self.removeAllIcon, 'Remove all', self, statusTip='Remove all clips from list',
                                       triggered=self.clearList, enabled=False)
        self.mediaInfoAction = QAction(self.mediaInfoIcon, 'Media information', self, triggered=self.mediaInfo,
                                       statusTip='View current media file\'s technical properties', enabled=False)
        self.openProjectAction = QAction(self.openProjectIcon, 'Open project file', self, triggered=self.openProject,
                                         statusTip='Open a previously saved project file (*.vcp or *.edl)',
                                         enabled=True)
        self.saveProjectAction = QAction(self.saveProjectIcon, 'Save project file', self, triggered=self.saveProject,
                                         statusTip='Save current work to a project file (*.vcp or *.edl)',
                                         enabled=False)
        self.viewLogsAction = QAction(self.viewLogsIcon, 'View log file', self, triggered=self.viewLogs,
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
                                        statusTip='Switch to fullscreen video', enabled=False)
        self.quitAction = QAction(self.quitIcon, 'Quit', self, triggered=self.parent.close,
                                  statusTip='Quit the application')

    def initToolbar(self) -> None:
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.playAction)
        self.toolbar.addAction(self.pauseAction)
        self.toolbar.addAction(self.cutStartAction)
        self.toolbar.addAction(self.cutEndAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.disableTooltips()
        self.toolbar.setLabelByType(self.settings.value('toolbarLabels', 'beside', type=str))

    def initMenus(self) -> None:
        self.appMenu.setLayoutDirection(Qt.LeftToRight)
        self.appMenu.addAction(self.openProjectAction)
        self.appMenu.addAction(self.saveProjectAction)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.settingsAction)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.fullscreenAction)
        self.appMenu.addAction(self.mediaInfoAction)
        self.appMenu.addAction(self.keyRefAction)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.viewLogsAction)
        self.appMenu.addAction(self.updateCheckAction)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.aboutQtAction)
        self.appMenu.addAction(self.aboutAction)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.quitAction)

        self.clipindex_contextmenu.addAction(self.moveItemUpAction)
        self.clipindex_contextmenu.addAction(self.moveItemDownAction)
        self.clipindex_contextmenu.addSeparator()
        self.clipindex_contextmenu.addAction(self.removeItemAction)
        self.clipindex_contextmenu.addAction(self.removeAllAction)

        self.clipindex_removemenu.addActions([self.removeItemAction, self.removeAllAction])
        self.clipindex_removemenu.aboutToShow.connect(self.initRemoveMenu)

        if sys.platform == 'win32':
            self.appMenu.setStyle(QStyleFactory.create('Fusion'))
            self.clipindex_contextmenu.setStyle(QStyleFactory.create('Fusion'))
            self.clipindex_removemenu.setStyle(QStyleFactory.create('Fusion'))

    def setRunningTime(self, runtime: str) -> None:
        self.runtimeLabel.setText('<div align="right">{}</div>'.format(runtime))
        self.runtimeLabel.setToolTip('total runtime: {}'.format(runtime))
        self.runtimeLabel.setStatusTip('total running time: {}'.format(runtime))

    @pyqtSlot()
    def showSettings(self):
        settingsDialog = SettingsDialog(self)
        settingsDialog.exec_()

    @pyqtSlot()
    def initRemoveMenu(self):
        self.removeItemAction.setEnabled(False)
        self.removeAllAction.setEnabled(False)
        if self.cliplist.count() > 0:
            self.removeAllAction.setEnabled(True)
            if len(self.cliplist.selectedItems()) > 0:
                self.removeItemAction.setEnabled(True)

    def itemMenu(self, pos: QPoint) -> None:
        globalPos = self.cliplist.mapToGlobal(pos)
        self.initRemoveMenu()
        self.moveItemUpAction.setEnabled(False)
        self.moveItemDownAction.setEnabled(False)
        index = self.cliplist.currentRow()
        if index != -1:
            if not self.inCut:
                if index > 0:
                    self.moveItemUpAction.setEnabled(True)
                if index < self.cliplist.count() - 1:
                    self.moveItemDownAction.setEnabled(True)
        self.clipindex_contextmenu.exec_(globalPos)

    def moveItemUp(self) -> None:
        index = self.cliplist.currentRow()
        tmpItem = self.clipTimes[index]
        del self.clipTimes[index]
        self.clipTimes.insert(index - 1, tmpItem)
        self.showText('clip moved up')
        self.renderClipIndex()

    def moveItemDown(self) -> None:
        index = self.cliplist.currentRow()
        tmpItem = self.clipTimes[index]
        del self.clipTimes[index]
        self.clipTimes.insert(index + 1, tmpItem)
        self.showText('clip moved down')
        self.renderClipIndex()

    def removeItem(self) -> None:
        index = self.cliplist.currentRow()
        del self.clipTimes[index]
        self.cliplist.takeItem(index)
        self.showText('clip removed')
        if self.mediaAvailable:
            if self.inCut and index == self.cliplist.count() - 1:
                self.inCut = False
                self.initMediaControls()
        elif len(self.clipTimes) == 0:
            self.initMediaControls(False)
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

    def projectFilters(self, savedialog: bool=False) -> str:
        if savedialog:
            return 'VidCutter Project (*.vcp);;MPlayer EDL (*.edl)'
        elif self.mediaAvailable:
            return 'Project files (*.edl *.vcp);;VidCutter Project (*.vcp);;MPlayer EDL (*.edl);;All files (*)'
        else:
            return 'VidCutter Project (*.vcp);;All files (*)'

    @staticmethod
    def mediaFilters(initial: bool=False) -> str:
        filters = 'All media files (*.{})'.format(' *.'.join(VideoService.config.filters.get('all')))
        if initial:
            return filters
        filters += ';;{};;All files (*)'.format(';;'.join(VideoService.config.filters.get('types')))
        return filters

    def openMedia(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self.parent,
                                                  caption='{} - Open media file'.format(qApp.applicationName()),
                                                  filter=self.mediaFilters(),
                                                  initialFilter=self.mediaFilters(True),
                                                  directory=(self.lastFolder if os.path.exists(self.lastFolder)
                                                             else QDir.homePath()),
                                                  options=(QFileDialog.DontUseNativeDialog
                                                           if not self.nativeDialogs else QFileDialog.Options()))
        if len(filename.strip()):
            self.lastFolder = QFileInfo(filename).absolutePath()
            self.loadMedia(filename)

    # noinspection PyUnusedLocal
    def openProject(self, checked: bool=False, project_file: str=None) -> None:
        initialFilter = 'Project files (*.edl *.vcp)' if self.mediaAvailable else 'VidCutter Project (*.vcp)'
        if project_file is None:
            project_file, _ = QFileDialog.getOpenFileName(self.parent,
                                                          caption='{} - Open project file'
                                                                  .format(qApp.applicationName()),
                                                          filter=self.projectFilters(),
                                                          initialFilter=initialFilter,
                                                          directory=(self.lastFolder if os.path.exists(self.lastFolder)
                                                                     else QDir.homePath()),
                                                          options=(QFileDialog.DontUseNativeDialog
                                                                   if not self.nativeDialogs
                                                                   else QFileDialog.Options()))
        if len(project_file.strip()):
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
                        line = str(line, encoding='utf-8')
                    except TypeError:
                        line = str(line)
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
                        mo = self.edlblock_re.match(line)
                        if mo:
                            start, stop, action = mo.groups()
                            clip_start = self.delta2QTime(int(float(start) * 1000))
                            clip_end = self.delta2QTime(int(float(stop) * 1000))
                            clip_image = self.captureImage(self.currentMedia, clip_start)
                            self.clipTimes.append([clip_start, clip_end, clip_image, ''])
                        else:
                            qApp.restoreOverrideCursor()
                            QMessageBox.critical(self.parent, 'Invalid project file',
                                                 'Invalid entry at line {0}:\n\n{1}'.format(linenum, line))
                            return
                linenum += 1
            self.cutStartAction.setEnabled(True)
            self.cutEndAction.setDisabled(True)
            self.seekSlider.setRestrictValue(0, False)
            self.inCut = False
            self.newproject = True
            QTimer.singleShot(2000, self.selectClip)
            qApp.restoreOverrideCursor()
            if project_file != os.path.join(QDir.tempPath(), self.parent.TEMP_PROJECT_FILE):
                self.showText('Project loaded')

    def saveProject(self, reboot: bool=False) -> None:
        if self.currentMedia is None:
            return
        for item in self.clipTimes:
            if len(item[3]):
                QMessageBox.critical(self.parent, 'Cannot save project',
                                     'The clip index currently contains at least one external media file which is '
                                     'not supported by current project file standards.\n\nSupport for external media '
                                     'may be added to the VCP (VidCutter Project file) format in the near future.')
                return
        project_file, _ = os.path.splitext(self.currentMedia)
        if reboot:
            project_save = os.path.join(QDir.tempPath(), self.parent.TEMP_PROJECT_FILE)
            ptype = 'VidCutter Project (*.vcp)'
        else:
            project_save, ptype = QFileDialog.getSaveFileName(self.parent,
                                                              caption=qApp.applicationName() + ' - Save project',
                                                              directory='{}.vcp'.format(project_file),
                                                              filter=self.projectFilters(True),
                                                              initialFilter='VidCutter Project (*.vcp)',
                                                              options=(QFileDialog.DontUseNativeDialog
                                                                       if not self.nativeDialogs
                                                                       else QFileDialog.Options()))
        if len(project_save.strip()):
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
                # noinspection PyUnresolvedReferences
                QTextStream(file) << '{0}\t{1}\t{2}\n'.format(self.delta2String(start_time),
                                                              self.delta2String(stop_time), 0)
            qApp.restoreOverrideCursor()
            self.projectSaved = True
            if not reboot:
                self.showText('Project file saved')

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
        if sys.platform.startswith('linux'):
            self.taskbar.clear()
        self.parent.setWindowTitle('{0} - {1}'.format(qApp.applicationName(), os.path.basename(self.currentMedia)))
        if not self.mediaAvailable:
            self.videoLayout.replaceWidget(self.novideoWidget, self.videoplayerWidget)
            self.novideoWidget.hide()
            self.novideoMovie.stop()
            self.novideoMovie.deleteLater()
            self.novideoWidget.deleteLater()
            self.videoplayerWidget.show()
            self.mediaAvailable = True
        try:
            self.videoService.setMedia(self.currentMedia)
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

    def playMedia(self) -> None:
        if self.mpvWidget.mpv.get_property('pause'):
            self.playAction.setVisible(False)
            self.pauseAction.setVisible(True)
        else:
            self.playAction.setVisible(True)
            self.pauseAction.setVisible(False)
        self.timeCounter.clearFocus()
        self.frameCounter.clearFocus()
        self.mpvWidget.pause()

    def showText(self, text: str, duration: int=3, override: bool=False) -> None:
        if self.mediaAvailable:
            if not self.osdButton.isChecked() and not override:
                return
            if len(text.strip()):
                self.mpvWidget.showText(text, duration)

    def initMediaControls(self, flag: bool=True) -> None:
        self.playAction.setEnabled(flag)
        self.saveAction.setEnabled(False)
        self.cutStartAction.setEnabled(flag)
        self.cutEndAction.setEnabled(False)
        self.mediaInfoAction.setEnabled(flag)
        self.mediainfoButton.setEnabled(flag)
        self.fullscreenButton.setEnabled(flag)
        self.fullscreenAction.setEnabled(flag)
        self.seekSlider.clearRegions()
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
            if sys.platform.startswith('linux'):
                self.taskbar.setProgress(float(position / self.seekSlider.maximum()))

    @pyqtSlot(float, int)
    def on_positionChanged(self, progress: float, frame: int) -> None:
        progress *= 1000
        if self.seekSlider.restrictValue < progress or progress == 0:
            self.seekSlider.setValue(int(progress))
            self.timeCounter.setTime(self.delta2QTime(int(progress)).toString(self.timeformat))
            self.frameCounter.setFrame(frame)

    @pyqtSlot(float, int)
    def on_durationChanged(self, duration: float, frames: int) -> None:
        duration *= 1000
        self.seekSlider.setRange(0, int(duration))
        self.timeCounter.setDuration(self.delta2QTime(int(duration)).toString(self.timeformat))
        self.frameCounter.setFrameCount(frames)

    @pyqtSlot(QListWidgetItem)
    @pyqtSlot()
    def selectClip(self, item: QListWidgetItem=None) -> None:
        # noinspection PyBroadException
        try:
            row = self.cliplist.row(item) if item is not None else 0
            if item is None:
                self.cliplist.item(row).setSelected(True)
            if not len(self.clipTimes[row][3]):
                self.seekSlider.selectRegion(row)
                self.setPosition(self.clipTimes[row][0].msecsSinceStartOfDay())
        except BaseException:
            pass

    def muteAudio(self) -> None:
        if self.mpvWidget.mpv.get_property('mute'):
            self.showText('Audio enabled')
            self.muteButton.setIcon(self.unmuteIcon)
            self.muteButton.setToolTip('Mute')
        else:
            self.showText('Audio disabled')
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
            self.showText('Thumbnails enabled')
            self.seekSlider.initStyle()
            if self.mediaAvailable:
                self.seekSlider.reloadThumbs()
        else:
            self.showText('Thumbnails disabled')
            self.seekSlider.removeThumbs()
            self.seekSlider.initStyle()

    @pyqtSlot(bool)
    def toggleConsole(self, checked: bool):
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
    def toggleSmartCut(self, checked: bool):
        self.smartcut = checked
        self.saveSetting('smartcut', self.smartcut)
        self.smartcutButton.setChecked(self.smartcut)
        self.showText('SmartCut {}'.format('enabled' if checked else 'disabled'))

    @pyqtSlot()
    def addExternalClips(self):
        clips, _ = QFileDialog.getOpenFileNames(self.parent,
                                                caption='{} - Add media files'.format(qApp.applicationName()),
                                                filter=self.mediaFilters(),
                                                initialFilter=self.mediaFilters(True),
                                                directory=(self.lastFolder if os.path.exists(self.lastFolder)
                                                           else QDir.homePath()),
                                                options=(QFileDialog.DontUseNativeDialog
                                                         if not self.nativeDialogs
                                                         else QFileDialog.Options()))
        if len(clips):
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
                self.showText('media file(s) added to index')
                self.renderClipIndex()

    def clipStart(self) -> None:
        # if os.getenv('DEBUG', False):
        #     self.logger.info('cut start position: %s' % self.seekSlider.value())
        starttime = self.delta2QTime(self.seekSlider.value())
        self.clipTimes.append([starttime, '', self.captureImage(self.currentMedia, starttime), ''])
        self.timeCounter.setMinimum(starttime.toString(self.timeformat))
        self.frameCounter.lockMinimum()
        self.cutStartAction.setDisabled(True)
        self.cutEndAction.setEnabled(True)
        self.clipindex_add.setDisabled(True)
        self.seekSlider.setRestrictValue(self.seekSlider.value(), True)
        self.inCut = True
        self.showText('start clip at {}'.format(starttime.toString(self.timeformat)))
        self.renderClipIndex()

    def clipEnd(self) -> None:
        # if os.getenv('DEBUG', False):
        #     self.logger.info('cut end position: %s' % self.seekSlider.value())
        item = self.clipTimes[len(self.clipTimes) - 1]
        endtime = self.delta2QTime(self.seekSlider.value())
        if endtime.__lt__(item[0]):
            QMessageBox.critical(self.parent, 'Invalid END Time',
                                 'The clip end time must come AFTER it\'s start time. Please try again.')
            return
        item[1] = endtime
        self.cutStartAction.setEnabled(True)
        self.cutEndAction.setDisabled(True)
        self.clipindex_add.setEnabled(True)
        self.timeCounter.setMinimum()
        self.seekSlider.setRestrictValue(0, False)
        self.inCut = False
        self.showText('end clip at {}'.format(endtime.toString(self.timeformat)))
        self.renderClipIndex()

    @pyqtSlot()
    def setProjectDirty(self, dirty: bool=True) -> None:
        self.projectDirty = dirty

    # noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
    @pyqtSlot(QModelIndex, int, int, QModelIndex, int)
    def syncClipList(self, parent: QModelIndex, start: int, end: int, destination: QModelIndex, row: int) -> None:
        if start < row:
            index = row - 1
        else:
            index = row
        clip = self.clipTimes.pop(start)
        self.clipTimes.insert(index, clip)
        if not len(clip[3]):
            self.seekSlider.switchRegions(start, index)
        self.showText('clip order updated')

    def renderClipIndex(self) -> None:
        self.cliplist.clear()
        self.seekSlider.clearRegions()
        self.totalRuntime = 0
        externalCount = 0
        for clip in self.clipTimes:
            endItem = ''
            if isinstance(clip[1], QTime):
                endItem = clip[1].toString(self.timeformat)
                self.totalRuntime += clip[0].msecsTo(clip[1])
            listitem = QListWidgetItem()
            if len(clip[3]):
                listitem.setToolTip(clip[3])
                externalCount += 1
            else:
                listitem.setToolTip('Drag to reorder clips')
            listitem.setStatusTip('Reorder clips with mouse drag & drop or right-click menu on the clip to be moved')
            listitem.setTextAlignment(Qt.AlignVCenter)
            listitem.setData(Qt.DecorationRole + 1, clip[2])
            listitem.setData(Qt.DisplayRole + 1, clip[0].toString(self.timeformat))
            listitem.setData(Qt.UserRole + 1, endItem)
            listitem.setData(Qt.UserRole + 2, clip[3])
            listitem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled)
            self.cliplist.addItem(listitem)
            if isinstance(clip[1], QTime) and not len(clip[3]):
                self.seekSlider.addRegion(clip[0].msecsSinceStartOfDay(), clip[1].msecsSinceStartOfDay())
        if len(self.clipTimes) and not self.inCut and (externalCount == 0 or externalCount > 1):
            self.saveAction.setEnabled(True)
            self.saveProjectAction.setEnabled(True)
        if self.inCut or len(self.clipTimes) == 0 or not isinstance(self.clipTimes[0][1], QTime):
            self.saveAction.setEnabled(False)
            self.saveProjectAction.setEnabled(False)
        self.setRunningTime(self.delta2QTime(self.totalRuntime).toString(self.runtimeformat))

    @staticmethod
    def delta2QTime(millisecs: int) -> QTime:
        secs = millisecs / 1000
        return QTime(int((secs / 3600) % 60), int((secs / 60) % 60), int(secs % 60), int((secs * 1000) % 1000))

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

    def captureImage(self, source: str, frametime: QTime, external: bool=False) -> QPixmap:
        return VideoService.captureFrame(source, frametime.toString(self.timeformat), external=external)

    def saveMedia(self) -> None:
        clips = len(self.clipTimes)
        source_file, source_ext = os.path.splitext(self.currentMedia if self.currentMedia is not None
                                                   else self.clipTimes[0][3])
        suggestedFilename = '{0}_EDIT{1}'.format(source_file, source_ext)
        filefilter = 'Video files (*{})'.format(source_ext)
        if clips > 0:
            self.finalFilename, _ = QFileDialog.getSaveFileName(parent=self.parent,
                                                                caption='{} - Save media file'
                                                                        .format(qApp.applicationName()),
                                                                directory=suggestedFilename, filter=filefilter,
                                                                options=(QFileDialog.DontUseNativeDialog
                                                                         if not self.nativeDialogs
                                                                         else QFileDialog.Options()))
            if not len(self.finalFilename.strip()):
                return
            file, ext = os.path.splitext(self.finalFilename)
            if len(ext) == 0 and len(source_ext):
                self.finalFilename += source_ext
            self.lastFolder = QFileInfo(self.finalFilename).absolutePath()
            self.saveAction.setDisabled(True)
            if self.smartcut:
                self.seekSlider.lockGUI(True)
                self.seekSlider.showProgress(6 if clips > 1 else 5)
                self.videoService.smartinit(clips)
                self.smartcutter(file, source_file, source_ext)
                return
            steps = 3 if clips > 1 else 2
            self.seekSlider.lockGUI(True)
            self.seekSlider.showProgress(steps)
            filename, filelist = '', []
            for clip in self.clipTimes:
                index = self.clipTimes.index(clip)
                self.seekSlider.updateProgress(index)
                if len(clip[3]):
                    filelist.append(clip[3])
                else:
                    duration = self.delta2QTime(clip[0].msecsTo(clip[1])).toString(self.timeformat)
                    filename = '{0}_{1}{2}'.format(file, '{0:0>2}'.format(index), source_ext)
                    if not self.keepClips:
                        filename = os.path.join(self.workFolder, os.path.basename(filename))
                    filelist.append(filename)
                    if not self.videoService.cut(source='{0}{1}'.format(source_file, source_ext),
                                                 output=filename,
                                                 frametime=clip[0].toString(self.timeformat),
                                                 duration=duration,
                                                 allstreams=True):
                        self.completeOnError('Failed to cut media file, assuming media is invalid or corrupt. '
                                             'Attempts are made to reindex and repair problematic media files even '
                                             'when keyframes are incorrectly set or missing.\n\nIf you feel this '
                                             'is a bug in the software then please let us know using the '
                                             'information provided in the About {} menu option so we may '
                                             'fix and improve for all users.'.format(qApp.applicationName()))
                        return
            self.joinMedia(filelist)

    def smartcutter(self, file: str, source_file: str, source_ext: str) -> None:
        self.smartcut_monitor = Munch(clips=[], results=[], externals=0)
        for clip in self.clipTimes:
            index = self.clipTimes.index(clip)
            if len(clip[3]):
                self.smartcut_monitor.clips.append(clip[3])
                self.smartcut_monitor.externals += 1
                if index == len(self.clipTimes):
                    self.smartmonitor()
            else:
                filename = '{0}_{1}{2}'.format(file, '{0:0>2}'.format(index), source_ext)
                if not self.keepClips:
                    filename = os.path.join(self.workFolder, os.path.basename(filename))
                self.smartcut_monitor.clips.append(filename)
                self.videoService.smartcut(index=index,
                                           source='{0}{1}'.format(source_file, source_ext),
                                           output=filename,
                                           start=VideoCutter.qtime2delta(clip[0]),
                                           end=VideoCutter.qtime2delta(clip[1]),
                                           allstreams=True)

    @pyqtSlot(bool, str)
    def smartmonitor(self, success: bool=None, outputfile: str=None) -> None:
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
            if self.videoService.isMPEGcodec(filelist[0]):
                self.logger.info('source file is MPEG based so join via MPEG-TS')
                rc = self.videoService.mpegtsJoin(filelist, self.finalFilename)
            if not rc or QFile(self.finalFilename).size() < 1000:
                self.logger.info('MPEG-TS based join failed, will retry using standard concat')
                rc = self.videoService.join(filelist, self.finalFilename, True)
            if not rc or QFile(self.finalFilename).size() < 1000:
                self.logger.info('join resulted in 0 length file, trying again without all stream mapping')
                self.videoService.join(filelist, self.finalFilename, False)
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
        self.seekSlider.updateProgress()
        self.saveAction.setEnabled(True)
        self.seekSlider.lockGUI(False)
        self.notify = JobCompleteNotification(
            self.finalFilename,
            self.sizeof_fmt(int(QFileInfo(self.finalFilename).size())),
            self.delta2QTime(self.totalRuntime).toString(self.runtimeformat),
            self.getAppIcon(encoded=True),
            self)
        self.notify.closed.connect(self.seekSlider.clearProgress)
        self.notify.exec_()
        if self.smartcut:
            QTimer.singleShot(1000, self.cleanup)
        self.setProjectDirty(False)

    @pyqtSlot(str)
    def completeOnError(self, errormsg: str) -> None:
        if self.smartcut:
            self.videoService.smartabort()
            QTimer.singleShot(1500, self.cleanup)
        self.seekSlider.lockGUI(False)
        self.seekSlider.clearProgress()
        self.saveAction.setEnabled(True)
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
            if self.videoService.mediainfo is None:
                self.logger.error('Error trying to load media information. mediainfo could not be found')
                sys.stderr.write('Error trying to load media information. mediainfo could not be found')
                QMessageBox.critical(self.parent, 'Could not find mediainfo tool',
                                     'The <b>mediainfo</b> command line tool could not be found on your system. '
                                     'This is required for the Media Information option '
                                     'to work.<br/><br/>If you are on Linux, you can solve '
                                     'this by installing the <b>mediainfo</b> package via your '
                                     'package manager.')
                return
            mediainfo = VideoInfo(media=self.currentMedia, parent=self)
            mediainfo.show()

    @pyqtSlot()
    def showKeyRef(self) -> None:
        shortcuts = QWidget(self)
        shortcuts.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        shortcuts.setObjectName('shortcuts')
        shortcuts.setAttribute(Qt.WA_DeleteOnClose, True)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(shortcuts.close)
        layout = QVBoxLayout()
        # noinspection PyArgumentList
        layout.addWidget(QLabel(pixmap=QPixmap(':/images/{}/shortcuts.png'.format(self.theme))))
        layout.addWidget(buttons)
        shortcuts.setLayout(layout)
        shortcuts.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        shortcuts.setContentsMargins(10, 10, 10, 10)
        shortcuts.setWindowModality(Qt.NonModal)
        shortcuts.setWindowTitle('Keyboard shortcuts')
        shortcuts.setMinimumWidth(400 if self.parent.scale == 'LOW' else 600)
        shortcuts.show()

    @pyqtSlot()
    def aboutApp(self) -> None:
        appInfo = About(self)
        appInfo.exec_()

    @staticmethod
    def getAppIcon(encoded: bool = False) -> Union[QIcon, str]:
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
    def sizeof_fmt(num: float, suffix: chr = 'B') -> str:
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Y', suffix)

    @staticmethod
    @pyqtSlot()
    def viewLogs() -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(logging.getLoggerClass().root.handlers[0].baseFilename))

    @pyqtSlot()
    def toggleFullscreen(self) -> None:
        if self.mediaAvailable:
            if self.mpvWidget.originalParent is not None:
                self.videoplayerLayout.insertWidget(0, self.mpvWidget)
                self.mpvWidget.originalParent = None
                self.parent.show()
            elif self.mpvWidget.parentWidget() != 0:
                self.parent.hide()
                self.videoplayerLayout.removeWidget(self.mpvWidget)
                self.mpvWidget.originalParent = self
                self.mpvWidget.setGeometry(qApp.desktop().screenGeometry(self))
                # noinspection PyTypeChecker
                self.mpvWidget.setParent(None)
                self.mpvWidget.showFullScreen()

    def toggleOSD(self, checked: bool) -> None:
        self.showText('On screen display {}'.format('enabled' if checked else 'disabled'), override=True)
        self.saveSetting('enableOSD', checked)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.mediaAvailable:

            if event.key() == Qt.Key_Space:
                self.playMedia()
                return

            if event.key() in {Qt.Key_F, Qt.Key_Escape}:
                self.mpvWidget.keyPressEvent(event)
                return

            if event.key() == Qt.Key_Home:
                self.setPosition(self.seekSlider.minimum())
                return

            if event.key() == Qt.Key_End:
                self.setPosition(self.seekSlider.maximum())
                return

            if event.key() == Qt.Key_Left:
                self.mpvWidget.frameBackStep()
                self.playAction.setVisible(True)
                self.pauseAction.setVisible(False)
                return

            if event.key() == Qt.Key_Down:
                if qApp.queryKeyboardModifiers() == Qt.ShiftModifier:
                    self.mpvWidget.seek(-self.level2Seek, 'relative+exact')
                else:
                    self.mpvWidget.seek(-self.level1Seek, 'relative+exact')
                return

            if event.key() == Qt.Key_Right:
                self.mpvWidget.frameStep()
                self.playAction.setVisible(True)
                self.pauseAction.setVisible(False)
                return

            if event.key() == Qt.Key_Up:
                if qApp.queryKeyboardModifiers() == Qt.ShiftModifier:
                    self.mpvWidget.seek(self.level2Seek, 'relative+exact')
                else:
                    self.mpvWidget.seek(self.level1Seek, 'relative+exact')
                return

            if event.key() in {Qt.Key_Return, Qt.Key_Enter} and \
                    (not self.timeCounter.hasFocus() and not self.frameCounter.hasFocus()):
                if self.cutStartAction.isEnabled():
                    self.clipStart()
                elif self.cutEndAction.isEnabled():
                    self.clipEnd()
                return
