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

from locale import setlocale, LC_NUMERIC

from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QDir, QFile, QFileInfo, QModelIndex, QPoint, QSize, Qt, QTextStream,
                          QTime, QUrl)
from PyQt5.QtGui import (QCloseEvent, QDesktopServices, QFont, QFontDatabase, QIcon, QKeyEvent,
                         QMouseEvent, QMovie, QPixmap)
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QActionGroup, qApp, QApplication, QDialogButtonBox,
                             QDoubleSpinBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QListWidgetItem, QMenu,
                             QMessageBox, QPushButton, QSizePolicy, QSlider, QStyle, QStyleFactory, QVBoxLayout,
                             QWidget, QWidgetAction)

from vidcutter.libs.videoservice import VideoService
from vidcutter.libs.widgets import FrameCounter, TimeCounter, VCProgressBar

from vidcutter.about import About
from vidcutter.updater import Updater
from vidcutter.videoframe import VideoFrame
from vidcutter.videoinfo import VideoInfo
from vidcutter.videolist import VideoList, VideoItem
from vidcutter.videoslider import VideoSlider, VideoSliderWidget
from vidcutter.videostyles import VideoStyles
from vidcutter.videotoolbar import VideoToolBar
import vidcutter.resources

try:
    import vidcutter.libs.mpv as mpv
    libmpv_error = False
except OSError:
    libmpv_error = True


class VideoCutter(QWidget):
    sliderMoved = pyqtSignal(int)
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)
    errorOccurred = pyqtSignal(str)

    def __init__(self, parent: QWidget):
        super(VideoCutter, self).__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        self.theme = self.parent.theme
        self.settings = self.parent.settings
        self.init_theme()
        if self.checkMPV():
            self.mediaPlayer = None
            self.videoService = VideoService(self)
            self.updater = Updater(self)
            self.latest_release_url = 'https://github.com/ozmartian/vidcutter/releases/latest'
            self.ffmpeg_installer = {
                'win32': {
                    64: 'https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-latest-win64-static.7z',
                    32: 'https://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-latest-win32-static.7z'
                },
                'darwin': {
                    64: 'http://evermeet.cx/pub/ffmpeg/snapshots',
                    32: 'http://evermeet.cx/pub/ffmpeg/snapshots'
                },
                'linux': {
                    64: 'https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-64bit-static.tar.xz',
                    32: 'https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-32bit-static.tar.xz'
                }
            }
            self.clipTimes = []
            self.inCut = False
            self.timeformat = 'hh:mm:ss.zzz'
            self.runtimeformat = 'hh:mm:ss'
            self.finalFilename = ''
            self.totalRuntime = 0
            self.frameRate = 0
            self.notifyInterval = 1000
            self.currentMedia, self.mediaAvailable, self.mpvError = None, False, False

            self.nativeDialogs = self.settings.value('nativeDialogs', True, type=bool)
            self.keepClips = self.settings.value('keepClips', False, type=bool)
            self.timelineThumbs = self.settings.value('timelineThumbs', True, type=bool)
            self.hardwareDecoding = self.settings.value('hwdec', 'auto', type=str) == 'auto'
            self.enableOSD = self.settings.value('enableOSD', True, type=bool)

            self.edlblock_re = re.compile(r'(\d+(?:\.?\d+)?)\s(\d+(?:\.?\d+)?)\s([01])')

            self.level1_spinner, self.level2_spinner = QDoubleSpinBox(self), QDoubleSpinBox(self)

            self.initIcons()
            self.initActions()
            self.toolbar = VideoToolBar(self, floatable=False, movable=False, iconSize=QSize(50, 53))
            self.initToolbar()

            self.appMenu, self.cliplistMenu = QMenu(self), QMenu(self)
            self.initMenus()

            self.seekSlider = VideoSlider(self, sliderMoved=self.sliderMoved.emit)
            self.seekSlider.sliderMoved.connect(self.sliderMoved.emit)
            self.sliderWidget = VideoSliderWidget(self, self.seekSlider)

            self.initNoVideo()

            self.cliplist = VideoList(self)
            self.cliplist.customContextMenuRequested.connect(self.itemMenu)
            self.cliplist.itemClicked.connect(self.positionAtClip)
            self.cliplist.model().rowsMoved.connect(self.syncClipList)

            listHeader = QLabel(pixmap=QPixmap(':/images/%s/clipindex.png' % self.theme, 'PNG'),
                                alignment=Qt.AlignCenter)
            listHeader.setObjectName('listHeader')

            self.runtimeLabel = QLabel('<div align="right">00:00:00</div>', textFormat=Qt.RichText)
            self.runtimeLabel.setObjectName('runtimeLabel')

            self.clipindexLayout = QVBoxLayout(spacing=0)
            self.clipindexLayout.setContentsMargins(0, 0, 0, 0)
            self.clipindexLayout.addWidget(listHeader)
            self.clipindexLayout.addWidget(self.cliplist)
            self.clipindexLayout.addWidget(self.runtimeLabel)

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
            countersLayout.addWidget(QLabel('TIME:', objectName='tcLabel'))
            countersLayout.addWidget(self.timeCounter)
            countersLayout.addStretch(1)
            countersLayout.addWidget(QLabel('FRAME:', objectName='fcLabel'))
            countersLayout.addWidget(self.frameCounter)
            countersLayout.addStretch(1)

            countersWidget = QWidget(self)
            countersWidget.setObjectName('counterwidgets')
            countersWidget.setContentsMargins(0, 0, 0, 0)
            countersWidget.setLayout(countersLayout)
            countersWidget.setMaximumHeight(28)

            self.initMPV()

            videoplayerLayout = QVBoxLayout(spacing=0)
            videoplayerLayout.setContentsMargins(0, 0, 0, 0)
            videoplayerLayout.addWidget(self.mpvFrame)
            videoplayerLayout.addWidget(countersWidget)

            self.videoplayerWidget = QWidget(self, visible=False, objectName='videoplayer')
            self.videoplayerWidget.setLayout(videoplayerLayout)

            # noinspection PyArgumentList
            self.thumbnailsButton = QPushButton(icon=self.thumbnailsIcon, flat=True, iconSize=QSize(16, 16),
                                                statusTip='Show timeline thumbnails', cursor=Qt.PointingHandCursor,
                                                toggled=self.seekSlider.toggleThumbnails, checkable=True,
                                                objectName='thumbnailsButton')
            if self.timelineThumbs:
                self.thumbnailsButton.setChecked(True)

            # noinspection PyArgumentList
            self.osdButton = QPushButton(icon=self.osdIcon, flat=True, iconSize=QSize(16, 16), checkable=True,
                                         statusTip='Toggle on-screen-display', cursor=Qt.PointingHandCursor,
                                         toggled=self.toggleOSD, objectName='osdButton')
            if self.enableOSD:
                self.osdButton.setChecked(True)

            if sys.platform == 'darwin':
                self.thumbnailsButton.setStyle(QStyleFactory.create('fusion'))
                self.osdButton.setStyle(QStyleFactory.create('fusion'))

            # noinspection PyArgumentList
            self.muteButton = QPushButton(objectName='muteButton', icon=self.unmuteIcon, flat=True, toolTip='Mute',
                                          statusTip='Toggle audio mute', iconSize=QSize(16, 16), clicked=self.muteAudio,
                                          cursor=Qt.PointingHandCursor)

            # noinspection PyArgumentList
            self.volumeSlider = QSlider(Qt.Horizontal, toolTip='Volume', statusTip='Adjust volume level',
                                        cursor=Qt.PointingHandCursor, value=self.parent.startupvol, minimum=0,
                                        maximum=130, sliderMoved=self.setVolume, objectName='volumeSlider')

            # noinspection PyArgumentList
            self.menuButton = QPushButton(self, toolTip='Menu', cursor=Qt.PointingHandCursor, flat=True,
                                          objectName='menuButton', statusTip='Click to view menu options')
            self.menuButton.setFixedSize(QSize(40, 42))
            self.menuButton.setMenu(self.appMenu)

            self.seekSlider.initStyle()

            toolbarLayout = QHBoxLayout()
            toolbarLayout.addWidget(self.toolbar)
            toolbarLayout.setContentsMargins(0, 0, 0, 0)

            toolbarGroup = QGroupBox()
            toolbarGroup.setLayout(toolbarLayout)
            toolbarGroup.setStyleSheet('border: 0;')

            controlsLayout = QHBoxLayout()
            controlsLayout.addSpacing(10)
            controlsLayout.addWidget(self.thumbnailsButton)
            controlsLayout.addWidget(self.osdButton)
            controlsLayout.addStretch(1)
            controlsLayout.addWidget(toolbarGroup)
            controlsLayout.addStretch(1)
            controlsLayout.addWidget(self.muteButton)
            controlsLayout.addSpacing(5)
            controlsLayout.addWidget(self.volumeSlider)
            controlsLayout.addSpacing(20)
            controlsLayout.addWidget(self.menuButton)
            controlsLayout.addSpacing(10)

            layout = QVBoxLayout(spacing=0)
            layout.setContentsMargins(10, 10, 10, 0)
            layout.addLayout(self.videoLayout)
            layout.addWidget(self.sliderWidget)
            layout.addSpacing(12)
            layout.addLayout(controlsLayout)

            self.setLayout(layout)

            self.sliderMoved.connect(self.setPosition)
            self.positionChanged.connect(self.on_positionChanged)
            self.durationChanged.connect(self.on_durationChanged)

    def checkMPV(self) -> bool:
        if not libmpv_error:
            return True
        pencolor1 = '#C681D5' if self.theme == 'dark' else '#642C68'
        pencolor2 = '#FFF' if self.theme == 'dark' else '#222'
        mbox = QMessageBox(self, objectName='genericdialog')
        mbox.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        mbox.setIconPixmap(QIcon(':/images/mpv.png').pixmap(128, 128))
        mbox.setWindowTitle('Missing libmpv library...')
        mbox.setMinimumWidth(500)
        mbox.setText('''
        <style>
            h1 {
                color: %s;
                font-family: 'Futura LT', sans-serif;
                font-weight: 400;
            }
            p, li { font-size: 15px; }
            p { color: %s; }
            li { color: %s; font-weight: bold; }
        </style>
        <table border="0" cellpadding="6" cellspacing="0" width="500">
        <tr><td>
            <h1>Cannot locate libmpv (MPV libraries) required for media playback</h1>
            <p>The app will now exit, please try again once you have installed
            libmpv via package installation or building from mpv source yourself.</p>
            <p>In most distributions libmpv can be found under package names like:
            <ul>
                <li>mpv <span style="font-size:12px;">(bundled with the mpv video player)</span></li>
                <li>libmpv1</li>
                <li>mpv-libs</li>
            </ul></p>
        </td></tr>
        </table>''' % (pencolor1, pencolor2, pencolor1))
        mbox.addButton(QMessageBox.Ok)
        sys.exit(mbox.exec_())

    def init_theme(self) -> None:
        VideoStyles.dark() if self.theme == 'dark' else VideoStyles.light()
        QFontDatabase.addApplicationFont(':/fonts/FuturaLT.ttf')
        QFontDatabase.addApplicationFont(':/fonts/OpenSans.ttf')
        QFontDatabase.addApplicationFont(':/fonts/OpenSansBold.ttf')
        VideoStyles.loadQSS(self.theme, self.parent.devmode)
        QApplication.setFont(QFont('Open Sans', 12 if sys.platform == 'darwin' else 10, 300))

    def logMPV(self, loglevel, component, message):
        log_msg = 'MPV {} - {}: {}'.format(loglevel, component, message)
        if loglevel in ('fatal', 'error'):
            self.logger.critical(log_msg)
            sys.stderr.write(log_msg)
            if loglevel == 'fatal' or 'file format' in message:
                self.errorOccurred.emit(message)
        else:
            self.logger.info(log_msg)

    def initMPV(self) -> None:
        setlocale(LC_NUMERIC, 'C')
        self.mpvFrame = VideoFrame(self)
        self.mediaPlayer = mpv.MPV(wid=int(self.mpvFrame.winId()),
                                   log_handler=self.logMPV,
                                   ytdl=False,
                                   pause=True,
                                   keep_open=True,
                                   idle=True,
                                   osc=False,
                                   osd_font='Futura LT',
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
                                   hr_seek=False,
                                   hr_seek_framedrop=True,
                                   volume=self.parent.startupvol,
                                   keepaspect=self.keepRatioAction.isChecked(),
                                   hwdec='auto' if self.hardwareDecodingAction.isChecked() else 'no')
        self.mediaPlayer.observe_property('time-pos', lambda prop, val: self.positionChanged.emit(val))
        self.mediaPlayer.observe_property('duration', lambda prop, val: self.durationChanged.emit(val))
        if os.getenv('DEBUG', False):
            self.mediaPlayer.msg_level = 'all=v'

    def initNoVideo(self) -> None:
        self.novideoWidget = QWidget(self, objectName='novideoWidget')
        self.novideoWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.novideoLabel = QLabel(alignment=Qt.AlignCenter)
        self.novideoLabel.setStyleSheet('margin-top:160px;')
        self.novideoMovie = QMovie(':/images/novideotext.gif')
        self.novideoMovie.frameChanged.connect(lambda: self.novideoLabel.setPixmap(self.novideoMovie.currentPixmap()))
        self.novideoMovie.start()
        novideoLayout = QVBoxLayout()
        novideoLayout.addStretch(1)
        novideoLayout.addWidget(self.novideoLabel)
        novideoLayout.addStretch(1)
        self.novideoWidget.setLayout(novideoLayout)

    def initIcons(self) -> None:
        self.appIcon = QIcon(':/images/vidcutter.png')
        self.openIcon = QIcon()
        self.openIcon.addFile(':/images/%s/toolbar-open.png' % self.theme, QSize(50, 53), QIcon.Normal)
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
        self.muteIcon = QIcon(':/images/%s/muted.png' % self.theme)
        self.unmuteIcon = QIcon(':/images/%s/unmuted.png' % self.theme)
        self.upIcon = QIcon(':/images/up.png')
        self.downIcon = QIcon(':/images/down.png')
        self.removeIcon = QIcon(':/images/remove.png')
        self.removeAllIcon = QIcon(':/images/remove-all.png')
        self.successIcon = QIcon(':/images/thumbsup.png')
        self.completePlayIcon = QIcon(':/images/complete-play.png')
        self.completeOpenIcon = QIcon(':/images/complete-open.png')
        self.completeRestartIcon = QIcon(':/images/complete-restart.png')
        self.completeExitIcon = QIcon(':/images/complete-exit.png')
        self.openProjectIcon = QIcon(':/images/open.png')
        self.saveProjectIcon = QIcon(':/images/save.png')
        self.mediaInfoIcon = QIcon(':/images/info.png')
        self.viewLogsIcon = QIcon(':/images/viewlogs.png')
        self.updateCheckIcon = QIcon(':/images/update.png')
        self.thumbsupIcon = QIcon(':/images/thumbs-up.png')
        self.keyRefIcon = QIcon(':/images/keymap.png')
        self.thumbnailsIcon = QIcon()
        self.thumbnailsIcon.addFile(':/images/%s/thumbnails-on.png' % self.theme, QSize(16, 16),
                                    QIcon.Normal, QIcon.On)
        self.thumbnailsIcon.addFile(':/images/%s/thumbnails-off.png' % self.theme, QSize(16, 16),
                                    QIcon.Normal, QIcon.Off)
        self.osdIcon = QIcon()
        self.osdIcon.addFile(':/images/%s/osd-on.png' % self.theme, QSize(16, 16), QIcon.Normal, QIcon.On)
        self.osdIcon.addFile(':/images/%s/osd-off.png' % self.theme, QSize(16, 16), QIcon.Normal, QIcon.Off)

    # noinspection PyArgumentList
    def initActions(self) -> None:
        self.themeAction = QActionGroup(self)
        self.zoomAction = QActionGroup(self)
        self.labelAction = QActionGroup(self)
        self.openAction = QAction(self.openIcon, 'Open\nMedia', self, statusTip='Open a media file',
                                  triggered=self.openMedia)
        self.playAction = QAction(self.playIcon, 'Play\nMedia', self, triggered=self.playMedia,
                                  statusTip='Play media file', enabled=False)
        self.pauseAction = QAction(self.pauseIcon, 'Pause\nMedia', self, visible=False, triggered=self.playMedia,
                                   statusTip='Pause currently playing media')
        self.cutStartAction = QAction(self.cutStartIcon, 'Clip\nStart', self, triggered=self.clipStart, enabled=False,
                                      statusTip='Set the start position of a new clip')
        self.cutEndAction = QAction(self.cutEndIcon, 'Clip\nEnd', self, triggered=self.clipEnd,
                                    enabled=False, statusTip='Set the end position of a new clip')
        self.saveAction = QAction(self.saveIcon, 'Save\nMedia', self, triggered=self.cutVideo, enabled=False,
                                  statusTip='Save clips to a new media file')
        self.moveItemUpAction = QAction(self.upIcon, 'Move up', self, statusTip='Move clip position up in list',
                                        triggered=self.moveItemUp, enabled=False)
        self.moveItemDownAction = QAction(self.downIcon, 'Move down', self, statusTip='Move clip position down in list',
                                          triggered=self.moveItemDown, enabled=False)
        self.removeItemAction = QAction(self.removeIcon, 'Remove clip', self, triggered=self.removeItem,
                                        statusTip='Remove selected clip from list', enabled=False)
        self.removeAllAction = QAction(self.removeAllIcon, 'Clear list', self, statusTip='Clear all clips from list',
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
        self.aboutQtAction = QAction('About Qt', self, statusTip='About Qt', triggered=qApp.aboutQt)
        self.aboutAction = QAction('About %s' % qApp.applicationName(), self, triggered=self.aboutApp,
                                   statusTip='About %s' % qApp.applicationName())
        self.keyRefAction = QAction(self.keyRefIcon, 'Keyboard shortcuts', self, triggered=self.showKeyRef,
                                    statusTip='View shortcut key bindings')
        self.lightThemeAction = QAction('Light', self.themeAction, checkable=True, checked=True,
                                        statusTip='Use a light colored theme to match your desktop')
        self.darkThemeAction = QAction('Dark', self.themeAction, checkable=True, checked=False,
                                       statusTip='Use a dark colored theme to match your desktop')
        self.qtrZoomAction = QAction('1:4 Quarter', self.zoomAction, checkable=True, checked=False,
                                     statusTip='Zoom to a quarter of the source video size')
        self.halfZoomAction = QAction('1:2 Half', self.zoomAction, statusTip='Zoom to half of the source video size',
                                      checkable=True, checked=False)
        self.origZoomAction = QAction('1:1 Original', self.zoomAction, checkable=True, checked=True,
                                      statusTip='Set to original source video zoom level')
        self.dblZoomAction = QAction('2:1 Double', self.zoomAction, checkable=True, checked=False,
                                     statusTip='Zoom to double the original source video size')
        self.besideLabelsAction = QAction('Labels next to buttons', self.labelAction, checkable=True,
                                          statusTip='Show labels on right side of toolbar buttons', checked=True)
        self.underLabelsAction = QAction('Labels under buttons', self.labelAction, checkable=True,
                                         statusTip='Show labels under toolbar buttons', checked=False)
        self.noLabelsAction = QAction('No labels', self.labelAction, statusTip='Do not show labels on toolbar',
                                      checkable=True, checked=False)
        self.keepRatioAction = QAction('Keep aspect ratio', self, checkable=True, triggered=self.setAspect,
                                       statusTip='Keep window aspect ratio when resizing the window', enabled=False)
        self.nativeDialogsAction = QAction('Use native dialogs', self, checkable=True, checked=self.nativeDialogs,
                                           statusTip='Use platform-native dialogs on file open & save operations')
        self.alwaysOnTopAction = QAction('Always on top', self, checkable=True, triggered=self.parent.set_always_on_top,
                                         statusTip='Keep app window on top of all other windows',
                                         checked=self.parent.ontop)
        self.keepClipsAction = QAction('Keep individual clips', self, checkable=True, checked=self.keepClips,
                                       statusTip='Keep the individual clips used to produce final media')
        self.hardwareDecodingAction = QAction('Hardware decoding', self, triggered=self.switchDecoding, checkable=True,
                                              checked=self.hardwareDecoding,
                                              statusTip='Enable hardware based video decoding for playback ' +
                                                        '(e.g. vdpau, vaapi, dxva2, d3d11, cuda)')
        if self.theme == 'dark':
            self.darkThemeAction.setChecked(True)
        else:
            self.lightThemeAction.setChecked(True)
        self.themeAction.triggered.connect(self.switchTheme)
        if self.settings.value('aspectRatio', 'keep', type=str) == 'keep':
            self.keepRatioAction.setChecked(True)
            self.zoomAction.setEnabled(False)
        self.zoomAction.triggered.connect(self.setZoom)

    def initToolbar(self) -> None:
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.playAction)
        self.toolbar.addAction(self.pauseAction)
        self.toolbar.addAction(self.cutStartAction)
        self.toolbar.addAction(self.cutEndAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.disableTooltips()
        self.labelAction.triggered.connect(self.toolbar.setLabels)
        self.toolbar.setLabelByType(self.settings.value('toolbarLabels', 'beside', type=str))

    def initMenus(self) -> None:
        labelsMenu = QMenu('Toolbar labels', self.appMenu)
        labelsMenu.addAction(self.besideLabelsAction)
        labelsMenu.addAction(self.underLabelsAction)
        labelsMenu.addAction(self.noLabelsAction)

        zoomMenu = QMenu('Zoom', self.appMenu)
        zoomMenu.addAction(self.qtrZoomAction)
        zoomMenu.addAction(self.halfZoomAction)
        zoomMenu.addAction(self.origZoomAction)
        zoomMenu.addAction(self.dblZoomAction)

        self.level1_spinner.setDecimals(1)
        self.level1_spinner.setRange(0.1, 999.9)
        self.level1_spinner.setSingleStep(0.1)
        self.level1_spinner.setSuffix(' secs')
        self.level1_spinner.setValue(self.settings.value('level1Seek', 2, type=float))
        level1_layout = QHBoxLayout()
        level1_layout.addStretch(1)
        level1_layout.addWidget(QLabel('Seek #1'))
        level1_layout.addWidget(self.level1_spinner)
        level1_layout.addStretch(1)
        level1Seek = QWidget(self)
        level1Seek.setLayout(level1_layout)
        level1seekAction = QWidgetAction(self)
        level1seekAction.setDefaultWidget(level1Seek)

        self.level2_spinner.setDecimals(1)
        self.level2_spinner.setRange(0.1, 999.9)
        self.level2_spinner.setSingleStep(0.1)
        self.level2_spinner.setSuffix(' secs')
        self.level2_spinner.setValue(self.settings.value('level2Seek', 5, type=float))
        level2_layout = QHBoxLayout()
        level2_layout.addStretch(1)
        level2_layout.addWidget(QLabel('Seek #2'))
        level2_layout.addWidget(self.level2_spinner)
        level2_layout.addStretch(1)
        level2Seek = QWidget(self)
        level2Seek.setLayout(level2_layout)
        level2seekAction = QWidgetAction(self)
        level2seekAction.setDefaultWidget(level2Seek)

        optionsMenu = QMenu('Settings...', self.appMenu)
        optionsMenu.addSection('Theme')
        optionsMenu.addAction(self.lightThemeAction)
        optionsMenu.addAction(self.darkThemeAction)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.keepClipsAction)
        optionsMenu.addSeparator()
        optionsMenu.addAction(level1seekAction)
        optionsMenu.addAction(level2seekAction)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.nativeDialogsAction)
        optionsMenu.addAction(self.alwaysOnTopAction)
        optionsMenu.addMenu(labelsMenu)
        optionsMenu.addSeparator()
        optionsMenu.addAction(self.hardwareDecodingAction)
        optionsMenu.addAction(self.keepRatioAction)
        optionsMenu.addMenu(zoomMenu)
        optionsMenu.aboutToShow.connect(self.clearSpinners)

        self.appMenu.setSeparatorsCollapsible(True)
        self.appMenu.addAction(self.openProjectAction)
        self.appMenu.addAction(self.saveProjectAction)
        self.appMenu.addSeparator()
        self.appMenu.addMenu(optionsMenu)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.mediaInfoAction)
        self.appMenu.addAction(self.keyRefAction)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.viewLogsAction)
        self.appMenu.addAction(self.updateCheckAction)
        self.appMenu.addSeparator()
        self.appMenu.addAction(self.aboutQtAction)
        self.appMenu.addAction(self.aboutAction)

        self.cliplistMenu.addAction(self.moveItemUpAction)
        self.cliplistMenu.addAction(self.moveItemDownAction)
        self.cliplistMenu.addSeparator()
        self.cliplistMenu.addAction(self.removeItemAction)
        self.cliplistMenu.addAction(self.removeAllAction)

        if sys.platform == 'win32':
            labelsMenu.setStyle(QStyleFactory.create('Fusion'))
            zoomMenu.setStyle(QStyleFactory.create('Fusion'))
            optionsMenu.setStyle(QStyleFactory.create('Fusion'))
            self.appMenu.setStyle(QStyleFactory.create('Fusion'))
            self.cliplistMenu.setStyle(QStyleFactory.create('Fusion'))

    def clearSpinners(self) -> None:
        for obj in (self.level1_spinner, self.level2_spinner):
            obj.clearFocus()
            obj.lineEdit().deselect()

    def setRunningTime(self, runtime: str) -> None:
        self.runtimeLabel.setText('<div align="right">%s</div>' % runtime)

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
        self.initMediaControls(True)

    def projectFilters(self) -> str:
        return 'VidCutter Project (*.vcp);;%sAll files (*.*)' \
               % ('MPlayer EDL (*.edl);;' if self.mediaAvailable else '')

    @staticmethod
    def mediaFilters() -> str:
        all_types = 'All media files (*.3gp, *.3g2, *.amv, * .avi, *.divx, *.div, *.flv, *.f4v, *.webm, *.mkv, ' + \
                    '*.mp3, *.mpa, *.mp1, *.mpeg, *.mpg, *.mpe, *.m1v, *.tod, *.mpv, *.m2v, *.ts, *.m2t, *.m2ts, ' + \
                    '*.mp4, *.m4v, *.mpv4, *.mod, *.mjpg, *.mjpeg, *.mov, *.qt, *.rm, *.rmvb, *.dat, *.bin, *.vob, ' + \
                    '*.wav, *.wma, *.wmv, *.asf, *.asx, *.xvid)'
        video_types = 'All video files (*.3gp, *.3g2, *.amv, * .avi, *.divx, *.div, *.flv, *.f4v, *.webm, *.mkv, ' + \
                      '*.mpeg, *.mpg, *.mpe, *.m1v, *.tod, *.mpv, *.m2v, *.ts, *.m2t, *.m2ts, ' + \
                      '*.mp4, *.m4v, *.mpv4, *.mod, *.mjpg, *.mjpeg, *.mov, *.qt, *.rm, *.rmvb, *.dat, *.bin, ' + \
                      '*.vob, *.wmv, *.asf, *.asx, *.xvid)'
        audio_types = 'All audio files (*.mp3, *.mpa, *.mp1, *.wav, *.wma)'
        specific_types = '3GPP files (*.3gp, *.3g2);;AMV files (*.amv);;AVI files (* .avi);;' + \
                         'DivX files (*.divx, *.div);;Flash files (*.flv, *.f4v);;WebM files (*.webm);;' + \
                         'MKV files (*.mkv);;MPEG Audio files (*.mp3, *.mpa, *.mp1);;' + \
                         'MPEG files (*.mpeg, *.mpg, *.mpe, *.m1v, *.tod);;' + \
                         'MPEG-2 files (*.mpv, *.m2v, *.ts, *.m2t, *.m2ts);;MPEG-4 files (*.mp4, *.m4v, *.mpv4);;' + \
                         'MOD files (*.mod);;MJPEG files (*.mjpg, *.mjpeg);;QuickTime files (*.mov, *.qt) ;;' + \
                         'RealMedia files (*.rm, *.rmvb);;VCD DAT files (*.dat);;VCD SVCD BIN/CUE images (*.bin);;' + \
                         'VOB files (*.vob);;Wave Audio files (*.wav);;Windows Media Audio files (*.wma);;' + \
                         'Windows Media files (*.wmv, *.asf, *.asx);;Xvid files (*.xvid)'
        return '%s;;%s;;%s;;%s;;All files (*.*)' % (all_types, video_types, audio_types, specific_types)

    def openMedia(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self.parent, caption='Select media file', filter=self.mediaFilters(),
                                                  directory=QDir.homePath(),
                                                  options=(QFileDialog.DontUseNativeDialog
                                                           if not self.nativeDialogsAction.isChecked()
                                                           else QFileDialog.Options()))
        if filename != '':
            self.loadMedia(filename)

    def openProject(self, checked: bool = False, project_file: str = None) -> None:
        if project_file is None:
            project_file, _ = QFileDialog.getOpenFileName(self.parent, caption='Select project file',
                                                          filter=self.projectFilters(),
                                                          initialFilter='VidCutter Project (*.vcp)',
                                                          directory=QDir.homePath(),
                                                          options=(QFileDialog.DontUseNativeDialog
                                                                   if not self.nativeDialogsAction.isChecked()
                                                                   else QFileDialog.Options()))
        if project_file.strip():
            file = QFile(project_file)
            info = QFileInfo(file)
            project_type = info.suffix()
            if not file.open(QFile.ReadOnly | QFile.Text):
                QMessageBox.critical(self.parent, 'Open project file',
                                     'Cannot read project file %s:\n\n%s' % (project_file, file.errorString()))
                return
            qApp.setOverrideCursor(Qt.WaitCursor)
            self.clipTimes.clear()
            linenum = 1
            while not file.atEnd():
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
                                             'Could not make sense of the selected project file. Try viewing it in a ' +
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
                            clip_image = self.captureImage(frametime=int(float(start) * 1000))
                            self.clipTimes.append([clip_start, clip_end, clip_image])
                        else:
                            qApp.restoreOverrideCursor()
                            QMessageBox.critical(self.parent, 'Invalid project file',
                                                 'Invalid entry at line %s:\n\n%s' % (linenum, line))
                            return
                linenum += 1
            self.cutStartAction.setEnabled(True)
            self.cutEndAction.setDisabled(True)
            self.seekSlider.setRestrictValue(0, False)
            self.inCut = False
            self.renderTimes()
            qApp.restoreOverrideCursor()
            self.showText('Project loaded...')

    def saveProject(self, filepath: str) -> None:
        if self.currentMedia is None:
            return
        project_file, _ = os.path.splitext(self.currentMedia)
        project_save, ptype = QFileDialog.getSaveFileName(self.parent, caption='Save project',
                                                          directory='%s.vcp' % project_file,
                                                          filter=self.projectFilters(),
                                                          initialFilter='VidCutter Project (*.vcp)',
                                                          options=(QFileDialog.DontUseNativeDialog
                                                                   if not self.nativeDialogsAction.isChecked()
                                                                   else QFileDialog.Options()))
        if project_save.strip():
            file = QFile(project_save)
            if not file.open(QFile.WriteOnly | QFile.Text):
                QMessageBox.critical(self.parent, 'Save project',
                                     'Cannot save project file at %s:\n\n%s' % (project_save, file.errorString()))
                return
            qApp.setOverrideCursor(Qt.WaitCursor)
            if ptype == 'VidCutter Project (*.vcp)':
                QTextStream(file) << '%s\n' % self.currentMedia
            for clip in self.clipTimes:
                start_time = timedelta(hours=clip[0].hour(), minutes=clip[0].minute(), seconds=clip[0].second(),
                                       milliseconds=clip[0].msec())
                stop_time = timedelta(hours=clip[1].hour(), minutes=clip[1].minute(), seconds=clip[1].second(),
                                      milliseconds=clip[1].msec())
                QTextStream(file) << '%s\t%s\t%d\n' % (self.delta2String(start_time), self.delta2String(stop_time), 0)
            qApp.restoreOverrideCursor()
            self.showText('Project was successfully saved...')

    def loadMedia(self, filename: str) -> None:
        if not os.path.exists(filename):
            return
        self.currentMedia = filename
        self.initMediaControls(True)
        self.cliplist.clear()
        self.clipTimes.clear()
        self.seekSlider.clearRegions()
        self.parent.setWindowTitle('%s - %s' % (qApp.applicationName(), os.path.basename(self.currentMedia)))
        if not self.mediaAvailable:
            self.videoLayout.replaceWidget(self.novideoWidget, self.videoplayerWidget)
            self.novideoMovie.stop()
            self.novideoMovie.deleteLater()
            self.novideoWidget.deleteLater()
            self.videoplayerWidget.show()
            self.mediaAvailable = True
        self.mediaPlayer.play(self.currentMedia)

    def playMedia(self) -> None:
        if self.mediaPlayer.pause:
            self.playAction.setVisible(False)
            self.pauseAction.setVisible(True)
        else:
            self.playAction.setVisible(True)
            self.pauseAction.setVisible(False)
        self.timeCounter.clearFocus()
        self.frameCounter.clearFocus()
        self.mediaPlayer.pause = not self.mediaPlayer.pause

    def showText(self, text: str, duration: int = 3, override: bool = False) -> None:
        if not self.osdButton.isChecked() and not override:
            return
        if len(text.strip()) and self.mediaAvailable:
            self.mediaPlayer.show_text(text, duration * 1000, 0)

    def initMediaControls(self, flag: bool = True) -> None:
        self.playAction.setEnabled(flag)
        self.saveAction.setEnabled(False)
        self.cutStartAction.setEnabled(flag)
        self.cutEndAction.setEnabled(False)
        self.mediaInfoAction.setEnabled(flag)
        self.keepRatioAction.setEnabled(flag)
        self.zoomAction.setEnabled(flag)
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
        if not self.mediaPlayer.seeking and position >= self.seekSlider.restrictValue:
            self.mediaPlayer.seek(self.delta2QTime(position).toString(self.timeformat),
                                  reference='absolute', precision='exact')

    @pyqtSlot(int)
    def on_positionChanged(self, progress: int) -> None:
        progress *= 1000
        if self.seekSlider.restrictValue < progress or progress == 0:
            self.seekSlider.setValue(progress)
            self.timeCounter.setTime(self.delta2QTime(progress).toString(self.timeformat))
            self.frameCounter.setFrame(self.mediaPlayer.estimated_frame_number)

    @pyqtSlot(int)
    def on_durationChanged(self, duration: int) -> None:
        duration *= 1000
        self.seekSlider.setRange(0, duration)
        self.timeCounter.setDuration(self.delta2QTime(duration).toString(self.timeformat))
        self.frameCounter.setFrameCount(self.mediaPlayer.estimated_frame_count)
        if self.thumbnailsButton.isChecked():
            self.seekSlider.timeline(self.currentMedia)

    @pyqtSlot(QListWidgetItem)
    def positionAtClip(self, item: QListWidgetItem) -> None:
        row = self.cliplist.indexFromItem(item).row()
        self.setPosition(self.clipTimes[row][0].msecsSinceStartOfDay())

    def muteAudio(self) -> None:
        if self.mediaPlayer.mute:
            self.showText('Audio enabled')
            self.muteButton.setIcon(self.unmuteIcon)
            self.muteButton.setToolTip('Mute')
        else:
            self.showText('Audio disabled')
            self.muteButton.setIcon(self.muteIcon)
            self.muteButton.setToolTip('Unmute')
        self.mediaPlayer.mute = not self.mediaPlayer.mute

    def setVolume(self, volume: int) -> None:
        if self.mediaAvailable:
            self.mediaPlayer.volume = volume

    @pyqtSlot(bool)
    def setAspect(self, checked: bool = True) -> None:
        self.mediaPlayer.keep_aspect(checked)
        self.zoomAction.setEnabled(checked)

    @pyqtSlot(QAction)
    def setZoom(self, action: QAction) -> None:
        if action == self.qtrZoomAction:
            level = -2
        elif action == self.halfZoomAction:
            level = -1
        elif action == self.dblZoomAction:
            level = 1
        else:
            level = 0
        self.mediaPlayer.video_zoom = level

    def clipStart(self) -> None:
        if os.getenv('DEBUG', False):
            print('cut start position: %s' % self.seekSlider.value())
        starttime = self.delta2QTime(self.mediaPlayer.playback_time * 1000)
        self.clipTimes.append([starttime, '', self.captureImage()])
        self.timeCounter.setMinimum(starttime.toString(self.timeformat))
        self.frameCounter.lockMinimum()
        self.cutStartAction.setDisabled(True)
        self.cutEndAction.setEnabled(True)
        self.seekSlider.setRestrictValue(self.seekSlider.value(), True)
        self.inCut = True
        self.showText('clip started at\n%s' % starttime.toString(self.timeformat))
        self.renderTimes()

    def clipEnd(self) -> None:
        if os.getenv('DEBUG', False):
            print('cut end position: %s' % self.seekSlider.value())
        item = self.clipTimes[len(self.clipTimes) - 1]
        endtime = self.delta2QTime(self.mediaPlayer.playback_time * 1000)
        if endtime.__lt__(item[0]):
            QMessageBox.critical(self.parent, 'Invalid END Time',
                                 'The clip end time must come AFTER it\'s start time. Please try again.')
            return
        item[1] = endtime
        self.cutStartAction.setEnabled(True)
        self.cutEndAction.setDisabled(True)
        self.timeCounter.setMinimum()
        self.seekSlider.setRestrictValue(0, False)
        self.inCut = False
        self.showText('clip ended at\n%s' % endtime.toString(self.timeformat))
        self.renderTimes()

    @pyqtSlot(QModelIndex, int, int, QModelIndex, int)
    def syncClipList(self, parent: QModelIndex, start: int, end: int, destination: QModelIndex, row: int) -> None:
        if start < row:
            index = row - 1
        else:
            index = row
        clip = self.clipTimes.pop(start)
        self.clipTimes.insert(index, clip)
        self.seekSlider.switchRegions(start, index)

    def renderTimes(self) -> None:
        self.cliplist.clear()
        self.seekSlider.clearRegions()
        if len(self.clipTimes) > 4:
            self.cliplist.setFixedWidth(210)
        else:
            self.cliplist.setFixedWidth(190)
        self.totalRuntime = 0
        for clip in self.clipTimes:
            endItem = ''
            if isinstance(clip[1], QTime):
                endItem = clip[1].toString(self.timeformat)
                self.totalRuntime += clip[0].msecsTo(clip[1])
            listitem = QListWidgetItem()
            listitem.setToolTip('Drag clip to reorder')
            listitem.setStatusTip('Reorder clips with drag and drop or right-click menu')
            listitem.setTextAlignment(Qt.AlignVCenter)
            listitem.setData(Qt.DecorationRole, clip[2])
            listitem.setData(Qt.DisplayRole, clip[0].toString(self.timeformat))
            listitem.setData(Qt.UserRole + 1, endItem)
            listitem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled)
            self.cliplist.addItem(listitem)
            if isinstance(clip[1], QTime):
                self.seekSlider.addRegion(clip[0].msecsSinceStartOfDay(), clip[1].msecsSinceStartOfDay())
        if len(self.clipTimes) and not self.inCut:
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
    def delta2String(td: timedelta) -> str:
        if td is None or td == timedelta.max:
            return ''
        else:
            return '%f' % (td.days * 86400 + td.seconds + td.microseconds / 1000000.)

    def captureImage(self, frametime=None) -> QPixmap:
        frametime = self.delta2QTime((self.mediaPlayer.playback_time * 1000) if frametime is None else frametime)
        imagecap = self.videoService.capture(self.currentMedia, frametime.toString(self.timeformat))
        if isinstance(imagecap, QPixmap):
            return imagecap

    def cutVideo(self) -> bool:
        clips = len(self.clipTimes)
        filename, filelist = '', []

        source_file, source_ext = os.path.splitext(self.currentMedia)
        if clips > 0:
            self.finalFilename, _ = QFileDialog.getSaveFileName(parent=self.parent, caption='Save video',
                                                                directory='%s_EDIT%s' % (source_file, source_ext),
                                                                filter='Video files (*%s)' % source_ext,
                                                                options=(QFileDialog.DontUseNativeDialog
                                                                         if not self.nativeDialogsAction.isChecked()
                                                                         else QFileDialog.Options()))
            if self.finalFilename == '':
                return False
            file, ext = os.path.splitext(self.finalFilename)
            if len(ext) == 0:
                ext = source_ext
                self.finalFilename += ext
            qApp.setOverrideCursor(Qt.WaitCursor)
            self.saveAction.setDisabled(True)
            self.showProgress(clips)
            index = 1
            self.progress.setText('Cutting media files...')
            qApp.processEvents()
            for clip in self.clipTimes:
                duration = self.delta2QTime(clip[0].msecsTo(clip[1])).toString(self.timeformat)
                filename = '%s_%s%s' % (file, '{0:0>2}'.format(index), ext)
                filelist.append(filename)
                self.videoService.cut(source='%s%s' % (source_file, source_ext),
                                      output=filename,
                                      frametime=clip[0].toString(self.timeformat),
                                      duration=duration,
                                      allstreams=True)
                if not QFile(filename).size():
                    self.logger.info('cut resulted in 0 length file, trying again without all stream mapping')
                    self.videoService.cut(source='%s%s' % (source_file, source_ext),
                                          output=filename,
                                          frametime=clip[0].toString(self.timeformat),
                                          duration=duration,
                                          allstreams=False)
                index += 1
            if len(filelist) > 1:
                rc = self.joinVideos(filelist, self.finalFilename, True)
                if not rc or not QFile(self.finalFilename).size():
                    self.logger.info('join() resulted in 0 length file, trying again without all stream mapping')
                    self.joinVideos(filelist, self.finalFilename, False)
                if not self.keepClipsAction.isChecked():
                    for f in filelist:
                        if os.path.isfile(f):
                            QFile.remove(f)
            else:
                QFile.remove(self.finalFilename)
                QFile.rename(filename, self.finalFilename)
            self.progress.setText('Complete...')
            self.progress.setValue(100)
            qApp.processEvents()
            self.progress.close()
            self.progress.deleteLater()
            qApp.restoreOverrideCursor()
            self.complete()
            return True
        return False

    def joinVideos(self, joinlist: list, filename: str, allstreams: bool = True) -> bool:
        listfile = os.path.normpath(os.path.join(os.path.dirname(joinlist[0]), '.vidcutter.list'))
        fobj = open(listfile, 'w')
        for file in joinlist:
            fobj.write('file \'%s\'\n' % file.replace("'", "\\'"))
        fobj.close()
        result = self.videoService.join(listfile, filename, allstreams)
        QFile.remove(listfile)
        return result

    @pyqtSlot()
    def mediaInfo(self) -> None:
        if self.mediaAvailable:
            if self.videoService.mediainfo is None:
                self.logger.error('Error trying to load media information. mediainfo could not be found')
                sys.stderr.write('Error trying to load media information. mediainfo could not be found')
                QMessageBox.critical(self, 'Could not find mediainfo tool',
                                     'The <b>mediainfo</b> command line tool could not be found on your system. ' +
                                     'This is required for the Media Information option ' +
                                     'to work.<br/><br/>If you are on Linux, you can solve ' +
                                     'this by installing the <b>mediainfo</b> package via your ' +
                                     'package manager.')
                return
            mediainfo = VideoInfo(media=self.currentMedia, parent=self)
            mediainfo.show()

    @pyqtSlot()
    def showKeyRef(self) -> None:
        shortcuts = QWidget(self)
        shortcuts.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        shortcuts.setObjectName('shortcuts')
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, parent=shortcuts)
        buttons.accepted.connect(shortcuts.hide)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(pixmap=QPixmap(':/images/%s/shortcuts.png' % self.theme)))
        layout.addWidget(buttons)
        shortcuts.setLayout(layout)
        shortcuts.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        shortcuts.setContentsMargins(10, 10, 10, 10)
        shortcuts.setWindowModality(Qt.WindowModal)
        shortcuts.setWindowTitle('Keyboard shortcuts')
        shortcuts.setMinimumWidth(400 if self.parent.scale == 'LOW' else 600)
        shortcuts.show()

    @pyqtSlot()
    def aboutApp(self) -> None:
        appInfo = About(self)
        appInfo.exec_()

    def showProgress(self, steps: int, label: str = 'Analyzing media...') -> None:
        self.progress = VCProgressBar(self)
        self.progress.setText(label)
        self.progress.setMinimumWidth(500)
        self.progress.setRange(0, steps)
        self.progress.show()
        for i in range(steps):
            self.progress.setValue(i)
            qApp.processEvents()
            time.sleep(1)

    def complete(self) -> None:
        info = QFileInfo(self.finalFilename)
        # noinspection PyArgumentList
        mbox = QMessageBox(windowTitle='Operation complete', minimumWidth=600, textFormat=Qt.RichText,
                           objectName='genericdialog2')
        mbox.setWindowFlags(Qt.Widget | Qt.WindowCloseButtonHint)
        mbox.setIconPixmap(self.thumbsupIcon.pixmap(150, 144))
        pencolor = '#C681D5' if self.theme == 'dark' else '#642C68'
        mbox.setText('''
    <style>
        h1 {
            color: %s;
            font-family: "Futura LT", sans-serif;
            font-weight: 400;
        }
        table.info {
            margin: 6px;
            margin-top: 15px;
            padding: 4px 15px;
        }
        td.label {
            font-size: 15px;
            font-weight: bold;
            text-align: right;
            color: %s;
        }
        td.value { font-size: 15px; }
    </style>
    <h1>Your media is ready!</h1>
    <table class="info" cellpadding="2" cellspacing="0" width="400">
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
    </table><br/>''' % (pencolor, pencolor, os.path.basename(self.finalFilename),
                        self.sizeof_fmt(int(info.size())),
                        self.delta2QTime(self.totalRuntime).toString(self.timeformat)))
        btn_play = mbox.addButton('Play', QMessageBox.ResetRole)
        btn_play.setIcon(self.completePlayIcon)
        btn_play.clicked.connect(self.openResult)
        btn_open = mbox.addButton('Open', QMessageBox.ResetRole)
        btn_open.setIcon(self.completeOpenIcon)
        btn_open.clicked.connect(lambda: self.openResult(pathonly=True))
        btn_exit = mbox.addButton('Exit', QMessageBox.AcceptRole)
        btn_exit.setIcon(self.completeExitIcon)
        btn_exit.clicked.connect(self.close)
        btn_restart = mbox.addButton('Restart', QMessageBox.AcceptRole)
        btn_restart.setIcon(self.completeRestartIcon)
        btn_restart.clicked.connect(self.parent.reboot)
        btn_continue = mbox.addButton('Continue', QMessageBox.AcceptRole)
        btn_continue.setIcon(self.style().standardIcon(QStyle.SP_DialogOkButton))
        btn_continue.clicked.connect(mbox.close)
        mbox.setDefaultButton(btn_continue)
        mbox.setEscapeButton(btn_continue)
        mbox.exec_()

    @staticmethod
    def sizeof_fmt(num: float, suffix: chr = 'B') -> str:
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Y', suffix)

    @pyqtSlot(bool)
    def openResult(self, pathonly: bool = False) -> None:
        if len(self.finalFilename) and os.path.exists(self.finalFilename):
            target = self.finalFilename if not pathonly else os.path.dirname(self.finalFilename)
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))

    @staticmethod
    @pyqtSlot()
    def viewLogs() -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(logging.getLoggerClass().root.handlers[0].baseFilename))

    @pyqtSlot(bool)
    def switchDecoding(self, checked: bool = True) -> None:
        self.mediaPlayer.hwdec = 'auto' if checked else 'no'

    @pyqtSlot(QAction)
    def switchTheme(self, action: QAction) -> None:
        if action == self.darkThemeAction:
            newtheme = 'dark'
        else:
            newtheme = 'light'
        if newtheme != self.theme:
            # noinspection PyArgumentList
            mbox = QMessageBox(icon=QMessageBox.NoIcon, windowTitle='Restart required', minimumWidth=500,
                               textFormat=Qt.RichText, objectName='genericdialog')
            mbox.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
            mbox.setText('''
                <style>
                    h1 {
                        color: %s;
                        font-family: "Futura LT", sans-serif;
                        font-weight: 400;
                    }
                    p { font-size: 15px; }
                </style>
                <h1>Warning</h1>
                <p>The application needs to be restarted in order to switch the theme. Ensure you have saved
                your project and no tasks are still in progress.</p>
                <p>Would you like to restart and switch themes now?</p>'''
                         % ('#C681D5' if self.theme == 'dark' else '#642C68'))
            mbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            mbox.setDefaultButton(QMessageBox.Yes)
            response = mbox.exec_()
            if response == QMessageBox.Yes:
                self.parent.reboot()
            else:
                if action == self.darkThemeAction:
                    self.lightThemeAction.setChecked(True)
                else:
                    self.darkThemeAction.setChecked(True)

    def ffmpeg_check(self) -> bool:
        valid = os.path.exists(self.videoService.backend) if self.videoService.backend is not None else False
        if not valid:
            if sys.platform == 'win32':
                exe = 'bin\\ffmpeg.exe'
            else:
                valid = os.path.exists(self.parent.get_path('bin/ffmpeg', override=True))
                exe = 'bin/ffmpeg'
            if sys.platform.startswith('linux'):
                link = self.ffmpeg_installer['linux'][self.parent.get_bitness()]
            else:
                link = self.ffmpeg_installer[sys.platform][self.parent.get_bitness()]
            QMessageBox.critical(None, 'Missing FFMpeg executable', '<style>li { margin: 1em 0; }</style>' +
                                 '<h3 style="color:#6A687D;">MISSING FFMPEG EXECUTABLE</h3>' +
                                 '<p>The FFMpeg utility is missing in your ' +
                                 'installation. It should have been installed when you first setup VidCutter.</p>' +
                                 '<p>You can easily fix this by manually downloading and installing it yourself by' +
                                 'following the steps provided below:</p><ol>' +
                                 '<li>Download the <b>static</b> version of FFMpeg from<br/>' +
                                 '<a href="%s" target="_blank"><b>this clickable link</b></a>.</li>' % link +
                                 '<li>Extract this file accordingly and locate the ffmpeg executable within.</li>' +
                                 '<li>Move or Cut &amp; Paste the executable to the following path on your system: ' +
                                 '<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;%s</li></ol>'
                                 % QDir.toNativeSeparators(self.parent.get_path(exe, override=True)) +
                                 '<p><b>NOTE:</b> You will most likely need Administrator rights (Windows) or ' +
                                 'root access (Linux/Mac) in order to do this.</p>')
        return valid

    def toggleMaximised(self) -> None:
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def toggleOSD(self, checked: bool) -> None:
        self.showText('On screen display %s' % ('enabled' if checked else 'disabled'), override=True)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.toggleMaximised()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_F:
            self.toggleMaximised()
            event.accept()
            return
        if self.mediaAvailable:
            if event.key() == Qt.Key_Left:
                self.mediaPlayer.frame_back_step()
            elif event.key() == Qt.Key_Down:
                if qApp.queryKeyboardModifiers() == Qt.ShiftModifier:
                    self.mediaPlayer.seek(-self.level2_spinner.value(), 'relative+exact')
                else:
                    self.mediaPlayer.seek(-self.level1_spinner.value(), 'relative+exact')
            elif event.key() == Qt.Key_Right:
                self.mediaPlayer.frame_step()
            elif event.key() == Qt.Key_Up:
                if qApp.queryKeyboardModifiers() == Qt.ShiftModifier:
                    self.mediaPlayer.seek(self.level2_spinner.value(), 'relative+exact')
                else:
                    self.mediaPlayer.seek(self.level1_spinner.value(), 'relative+exact')
            elif event.key() == Qt.Key_Home:
                self.mediaPlayer.time_pos = 0
            elif event.key() == Qt.Key_End:
                self.setPosition(self.seekSlider.maximum() - 1)
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and (
                        not self.timeCounter.hasFocus() and not self.frameCounter.hasFocus()):
                if self.cutStartAction.isEnabled():
                    self.clipStart()
                elif self.cutEndAction.isEnabled():
                    self.clipEnd()
            elif event.key() == Qt.Key_Space:
                self.playMedia()
            event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.parentWidget().closeEvent(event)
