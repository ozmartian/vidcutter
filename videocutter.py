#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shlex
import signal
import subprocess
import sys
import tempfile

from PyQt5.QtCore import QDir, QEvent, QSize, Qt, QTime, QUrl
from PyQt5.QtGui import QFontDatabase, QIcon, QPalette, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QApplication, QFileDialog, QHBoxLayout,
                             QLabel, QListWidget, QListWidgetItem,
                             QMenu, QMessageBox, QPushButton, QSizePolicy, QSlider,
                             QStyle, QToolBar, QVBoxLayout, QWidget, qApp)

from .ffmpy import FFmpeg
from .videoslider import VideoSlider
from .videowidget import VideoWidget


class VideoCutter(QWidget):
    def __init__(self, parent=None):
        super(VideoCutter, self).__init__(parent)
        self.parent = parent
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videoWidget = VideoWidget()

        QFontDatabase.addApplicationFont(os.path.join(self.getFilePath(), 'fonts', 'DroidSansMono.ttf'))

        self.FFMPEG_bin = 'ffmpeg'
        if sys.platform == 'win32':
            self.FFMPEG_bin = os.path.join(self.getFilePath(), 'bin', 'ffmpeg.exe')

        self.clipTimes = []
        self.inCut = False
        self.timeformat = 'hh:mm:ss'
        self.finalFilename = ''

        self.initIcons()
        self.initActions()
        self.initToolbar()
        self.initMenu()

        self.positionSlider = VideoSlider(objectName='VideoSlider', sliderMoved=self.setPosition)
        self.positionSlider.installEventFilter(self)

        self.movieLabel = QLabel(alignment=Qt.AlignCenter, autoFillBackground=True, textFormat=Qt.RichText,
                                 sizePolicy=QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored),
                                 styleSheet='font-size:20px; font-weight:bold; font-family:sans-serif;')
        self.movieLabel.setBackgroundRole(QPalette.Dark)
        self.movieLabel.setAlignment(Qt.AlignCenter)
        self.movieLabel.setPixmap(QPixmap(os.path.join(self.getFilePath(), 'icons', 'novideo.png'), 'PNG'))
        self.movieLoaded = False

        self.cliplist = QListWidget()
        self.cliplist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cliplist.setUniformItemSizes(True)
        self.cliplist.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.cliplist.setFixedWidth(180)
        self.cliplist.setIconSize(QSize(100, 70))
        self.cliplist.setAlternatingRowColors(True)
        self.cliplist.setDragDropMode(QAbstractItemView.InternalMove)
        self.cliplist.setStyleSheet('QListView::item { margin:10px 5px; }')
        self.cliplist.model().rowsMoved.connect(self.syncClipList)
        self.cliplist.customContextMenuRequested.connect(self.itemMenu)

        listHeader = QLabel(pixmap=QPixmap(os.path.join(self.getFilePath(), 'icons', 'clipindex.png')), alignment=Qt.AlignCenter)
        listHeader.setStyleSheet('padding:5px; padding-top:8px; border:1px solid #b9b9b9; border-bottom:none; background-color:qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF, stop: 0.5 #EAEAEA, stop: 0.6 #EAEAEA stop:1 #FFF);')

        clipLayout = QVBoxLayout()
        clipLayout.setContentsMargins(0, 0, 0, 0)
        clipLayout.setSpacing(0)
        clipLayout.addWidget(listHeader)
        clipLayout.addWidget(self.cliplist)

        self.videoLayout = QHBoxLayout()
        self.videoLayout.setContentsMargins(0, 0, 0, 0)
        self.videoLayout.addWidget(self.movieLabel)
        self.videoLayout.addLayout(clipLayout)

        self.timeCounter = QLabel('00:00:00 / 00:00:00')
        self.timeCounter.setStyleSheet('font-family:Droid Sans Mono; font-size:10pt; color:#666; margin-top:-2px; margin-right:150px; margin-bottom:6px;')

        timerLayout = QHBoxLayout()
        timerLayout.addStretch(1)
        timerLayout.addWidget(self.timeCounter)
        timerLayout.addStretch(1)

        self.menuButton = QPushButton(icon=self.aboutIcon, flat=True, toolTip='About',
                                      statusTip='About %s' % qApp.applicationName(),
                                      iconSize=QSize(24, 24), cursor=Qt.PointingHandCursor)
        self.menuButton.setMenu(self.aboutMenu)

        self.muteButton = QPushButton(icon=self.unmuteIcon, flat=True, toolTip='Mute', statusTip='Toggle audio mute',
                                      cursor=Qt.PointingHandCursor, clicked=self.muteAudio)

        self.volumeSlider = QSlider(Qt.Horizontal, toolTip='Volume', statusTip='Adjust volume level',
                                    cursor=Qt.PointingHandCursor,
                                    value=50, sizePolicy=QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum),
                                    minimum=0, maximum=100, sliderMoved=self.setVolume)

        controlsLayout = QHBoxLayout()
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.toolbar)
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.muteButton)
        controlsLayout.addWidget(self.volumeSlider)
        controlsLayout.addSpacing(4)
        controlsLayout.addWidget(self.menuButton)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 4)
        layout.addLayout(self.videoLayout)
        layout.addLayout(timerLayout)
        layout.addWidget(self.positionSlider)
        layout.addLayout(controlsLayout)

        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def initIcons(self):
        self.appIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'videocutter.png'))
        self.openIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'open.png'))
        self.playIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'play.png'))
        self.pauseIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'pause.png'))
        self.cutStartIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'start.png'))
        self.cutEndIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'end.png'))
        self.saveIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'save.png'))
        self.muteIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'muted.png'))
        self.unmuteIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'unmuted.png'))
        self.upIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'up.png'))
        self.downIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'down.png'))
        self.removeIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'remove.png'))
        self.removeAllIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'remove-all.png'))
        self.successIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'success.png'))
        self.aboutIcon = QIcon(os.path.join(self.getFilePath(), 'icons', 'about.png'))

    def initActions(self):
        self.openAction = QAction(self.openIcon, '&Open', self, statusTip='Select video', triggered=self.openFile)
        self.playAction = QAction(self.playIcon, '&Play', self, statusTip='Play video', triggered=self.playVideo, enabled=False)
        self.cutStartAction = QAction(self.cutStartIcon, 'Set St&art', self, toolTip='Set Start', statusTip='Set start marker', triggered=self.cutStart, enabled=False)
        self.cutEndAction = QAction(self.cutEndIcon, 'Set &End', self, statusTip='Set end marker', triggered=self.cutEnd, enabled=False)
        self.saveAction = QAction(self.saveIcon, 'Sa&ve', self, statusTip='Save new video', triggered=self.cutVideo, enabled=False)
        self.moveItemUpAction = QAction(self.upIcon, 'Move Up', self, statusTip='Move clip position up in list', triggered=self.moveItemUp, enabled=False)
        self.moveItemDownAction = QAction(self.downIcon, 'Move Down', self, statusTip='Move clip position down in list', triggered=self.moveItemDown, enabled=False)
        self.removeItemAction = QAction(self.removeIcon, 'Remove clip', self, statusTip='Remove selected clip from list', triggered=self.removeItem, enabled=False)
        self.removeAllAction = QAction(self.removeAllIcon, 'Clear list', self, statusTip='Clear all clips from list', triggered=self.clearList, enabled=False)
        self.aboutAction = QAction('About %s' % qApp.applicationName(), self, statusTip='Credits and acknowledgements', triggered=self.aboutInfo)
        self.aboutQtAction = QAction('About Qt', self, statusTip='About Qt', triggered=qApp.aboutQt)
        self.mediaInfoAction = QAction('Media Information', self, statusTip='Media information from loaded video file', triggered=self.mediaInfo, enabled=False)

    def initToolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet('QToolBar QToolButton { min-width:82px; margin-left:10px; margin-right:10px; font-size:14px; }')
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.playAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.cutStartAction)
        self.toolbar.addAction(self.cutEndAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.saveAction)

    def initMenu(self):
        self.aboutMenu = QMenu()
        self.aboutMenu.addAction(self.mediaInfoAction)
        self.aboutMenu.addSeparator()
        self.aboutMenu.addAction(self.aboutQtAction)
        self.aboutMenu.addAction(self.aboutAction)

    def itemMenu(self, pos):
        globalPos = self.cliplist.mapToGlobal(pos)
        self.cliplistMenu = QMenu()
        self.cliplistMenu.addAction(self.moveItemUpAction)
        self.cliplistMenu.addAction(self.moveItemDownAction)
        self.cliplistMenu.addSeparator()
        self.cliplistMenu.addAction(self.removeItemAction)
        self.cliplistMenu.addAction(self.removeAllAction)
        self.moveItemUpAction.setEnabled(False)
        self.moveItemDownAction.setEnabled(False)
        self.removeItemAction.setEnabled(False)
        self.removeAllAction.setEnabled(False)
        index = self.cliplist.currentRow()
        if self.cliplist.count() > 0:
            self.removeAllAction.setEnabled(True)
        if index != -1:
            if not self.inCut:
                if index > 0:
                    self.moveItemUpAction.setEnabled(True)
                if index < self.cliplist.count() - 1:
                    self.moveItemDownAction.setEnabled(True)
            if self.cliplist.count() > 0:
                self.removeItemAction.setEnabled(True)
        self.cliplistMenu.exec_(globalPos)

    def moveItemUp(self):
        index = self.cliplist.currentRow()
        tmpItem = self.clipTimes[index]
        del self.clipTimes[index]
        self.clipTimes.insert(index - 1, tmpItem)
        self.renderTimes()

    def moveItemDown(self):
        index = self.cliplist.currentRow()
        tmpItem = self.clipTimes[index]
        del self.clipTimes[index]
        self.clipTimes.insert(index + 1, tmpItem)
        self.renderTimes()

    def removeItem(self):
        index = self.cliplist.currentRow()
        del self.clipTimes[index]
        self.renderTimes()
        self.initMediaControls()
        if len(self.clipTimes) > 0:
            self.saveAction.setEnabled(True)

    def clearList(self):
        self.clipTimes.clear()
        self.cliplist.clear()
        self.inCut = False
        self.renderTimes()
        self.initMediaControls()

    def mediaInfo(self):
        if self.mediaPlayer.isMetaDataAvailable():
            content = '<table cellpadding="4">'
            for key in self.mediaPlayer.availableMetaData():
                val = self.mediaPlayer.metaData(key)
                if type(val) is QSize:
                    val = '%s x %s' % (val.width(), val.height())
                content += '<tr><td align="right"><b>%s:</b></td><td>%s</td></tr>\n' % (key, val)
            content += '</table>'
            mbox = QMessageBox(windowTitle='Media Information', windowIcon=self.parent.windowIcon(), textFormat=Qt.RichText)
            mbox.setText('<b>%s</b>' % os.path.basename(self.mediaPlayer.currentMedia().canonicalUrl().toLocalFile()))
            mbox.setInformativeText(content)
            mbox.exec_()
        else:
            QMessageBox.critical(self, 'Could not retrieve media information', 'There was a problem in tring to retrieve media information.\n\nThis DOES NOT mean there is a problem with the file and you should be able to continue using it.')

    def aboutInfo(self):
        aboutApp = '''<style>
    a { color:#441d4e; text-decoration:none; font-weight:bold; }
    a:hover { text-decoration:underline; }
</style>
<h1>%s</h1>
<h3 style="font-weight:normal;"><b>Version:</b> %s</h3>
<p>Copyright &copy; 2016 <a href="mailto:pete@ozmartians.com">Pete Alexandrou</a></p>
<p style="font-size:13px">
    A special thanks & acknowledgements to the teams behind the <b>PyQt5</b> and <b>FFmpeg</b> software projects.
    None of this would be possible without you!
</p>
<p style="font-size:11px">
    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.
</p>''' % (qApp.applicationName(), qApp.applicationVersion())
        QMessageBox.about(self, 'About %s' % qApp.applicationName(), aboutApp)

    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, caption='Select video', directory=QDir.homePath())
        if filename != '':
            self.loadFile(filename)

    def loadFile(self, filename):
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
        self.initMediaControls(True)
        self.cliplist.clear()
        self.clipTimes = []
        self.parent.setWindowTitle('%s %s - %s' % (qApp.applicationName(), qApp.applicationVersion(), os.path.basename(filename)))
        if not self.movieLoaded:
            self.videoLayout.replaceWidget(self.movieLabel, self.videoWidget)
            self.movieLabel.deleteLater()
            self.videoWidget.show()
            # self.mediaPlayer.play()
            self.mediaPlayer.pause()
            self.movieLoaded = True

    def playVideo(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def initMediaControls(self, flag=True):
        self.playAction.setEnabled(flag)
        self.saveAction.setEnabled(False)
        self.cutStartAction.setEnabled(flag)
        self.cutEndAction.setEnabled(False)
        self.mediaInfoAction.setEnabled(flag)
        if flag:
            self.positionSlider.setRestrictValue(0)

    def setPosition(self, position):
        # if self.mediaPlayer.state() == QMediaPlayer.StoppedState:
        #     self.mediaPlayer.play()
        #     self.mediaPlayer.pause()
        self.mediaPlayer.setPosition(position)

    def positionChanged(self, progress):
        self.positionSlider.setValue(progress)
        currentTime = self.deltaToQTime(progress)
        totalTime = self.deltaToQTime(self.mediaPlayer.duration())
        self.timeCounter.setText('%s / %s' % (currentTime.toString(self.timeformat), totalTime.toString(self.timeformat)))

    def mediaStateChanged(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playAction.setIcon(self.pauseIcon)
            self.playAction.setText('Pause')
        else:
            self.playAction.setIcon(self.playIcon)
            self.playAction.setText('Play')

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def muteAudio(self, muted):
        if self.mediaPlayer.isMuted():
            self.mediaPlayer.setMuted(not self.mediaPlayer.isMuted())
            self.muteButton.setIcon(self.unmuteIcon)
            self.muteButton.setToolTip('Mute')
        else:
            self.mediaPlayer.setMuted(not self.mediaPlayer.isMuted())
            self.muteButton.setIcon(self.muteIcon)
            self.muteButton.setToolTip('Unmute')

    def setVolume(self, volume):
        self.mediaPlayer.setVolume(volume)

    def toggleFullscreen(self):
        self.videoWidget.setFullScreen(not self.videoWidget.isFullScreen())

    def cutStart(self):
        self.clipTimes.append([self.deltaToQTime(self.mediaPlayer.position()), '', self.captureImage()])
        self.cutStartAction.setDisabled(True)
        self.cutEndAction.setEnabled(True)
        self.positionSlider.setRestrictValue(self.positionSlider.value())
        self.inCut = True
        self.renderTimes()

    def cutEnd(self):
        item = self.clipTimes[len(self.clipTimes) - 1]
        selected = self.deltaToQTime(self.mediaPlayer.position())
        if selected.__lt__(item[0]):
            QMessageBox.critical(self, 'Invalid END Time', 'The clip end time must come AFTER it\'s start time. Please try again.')
            return
        item[1] = selected
        self.cutStartAction.setEnabled(True)
        self.cutEndAction.setDisabled(True)
        self.positionSlider.setRestrictValue(0)
        self.inCut = False
        self.renderTimes()

    def syncClipList(self, parent, start, end, destination, row):
        if start < row:
            index = row - 1
        else:
            index = row
        clip = self.clipTimes.pop(start)
        self.clipTimes.insert(index, clip)

    def renderTimes(self):
        self.cliplist.clear()
        self.positionSlider.setCutMode(self.inCut)
        if len(self.clipTimes) > 4:
            self.cliplist.setFixedWidth(195)
        else:
            self.cliplist.setFixedWidth(180)
        for item in self.clipTimes:
            endItem = ''
            if type(item[1]) is QTime:
                endItem = item[1].toString(self.timeformat)
            listitem = QListWidgetItem()
            listitem.setTextAlignment(Qt.AlignVCenter)
            if type(item[2]) is QPixmap:
                listitem.setIcon(QIcon(item[2]))
            self.cliplist.addItem(listitem)
            marker = QLabel('<style>b { font-size:8pt; } p { margin:5px; }</style><p><b>START</b><br/>%s</p><p><b>END</b><br/>%s</p>' % (item[0].toString(self.timeformat), endItem))
            self.cliplist.setItemWidget(listitem, marker)
            listitem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled)
        if len(self.clipTimes):
            self.saveAction.setEnabled(True)
        if len(self.clipTimes) == 0 or not type(self.clipTimes[0][1]) is QTime:
            self.saveAction.setEnabled(False)

    @staticmethod
    def deltaToQTime(millisecs):
        secs = millisecs / 1000
        return QTime((secs / 3600) % 60, (secs / 60) % 60, secs % 60, (secs * 1000) % 1000)

    def captureImage(self):
        frametime = self.deltaToQTime(self.mediaPlayer.position()).addSecs(1).toString(self.timeformat)
        if sys.platform == 'win32':
            fd, imagecap = tempfile.mkstemp(suffix='.jpg')
            try:
                os.write(fd, b'dummy data')
                os.close(fd)
                ff = FFmpeg(
                    executable=self.FFMPEG_bin,
                    inputs={self.mediaPlayer.currentMedia().canonicalUrl().toLocalFile(): '-ss %s' % frametime},
                    outputs={imagecap: '-vframes 1 -s 100x70 -y'}
                )
                ff.run()
                capres = QPixmap(imagecap, 'JPG')
            finally:
                os.remove(imagecap)
        else:
            with tempfile.NamedTemporaryFile(suffix='.jpg') as imagecap:
                ff = FFmpeg(
                    executable=self.FFMPEG_bin,
                    inputs={self.mediaPlayer.currentMedia().canonicalUrl().toLocalFile(): '-ss %s' % frametime},
                    outputs={imagecap.name: '-vframes 1 -s 100x70 -y'}
                )
                ff.run()
                capres = QPixmap(imagecap.name, 'JPG')
        return capres

    def cutVideo(self):
        self.setCursor(Qt.BusyCursor)
        filename = ''
        filelist = []
        source = self.mediaPlayer.currentMedia().canonicalUrl().toLocalFile()
        _, sourceext = os.path.splitext(source)
        if len(self.clipTimes):
            self.finalFilename, _ = QFileDialog.getSaveFileName(parent=self, caption='Save video', directory=source,
                                                                filter='Video files (*%s)' % sourceext)
            if self.finalFilename != '':
                file, ext = os.path.splitext(self.finalFilename)
                index = 1
                for clip in self.clipTimes:
                    runtime = self.deltaToQTime(clip[0].msecsTo(clip[1])).toString(self.timeformat)
                    filename = '%s_%s%s' % (file, '{0:0>2}'.format(index), ext)
                    filelist.append(filename)
                    ff = FFmpeg(
                        executable=self.FFMPEG_bin,
                        inputs={source: None},
                        outputs={filename: '-ss %s -t %s -vcodec copy -acodec copy -y' % (clip[0].toString(self.timeformat), runtime)}
                    )
                    ff.run()
                    index += 1
                if len(filelist) > 1:
                    self.joinVideos(filelist, self.finalFilename)
                else:
                    try:
                        os.remove(self.finalFilename)
                        os.rename(filename, self.finalFilename)
                    except:
                        pass
                self.unsetCursor()
                msgbox = QMessageBox()
                msgbox.setWindowTitle('Success')
                msgbox.setWindowIcon(self.parent.windowIcon())
                msgbox.setIconPixmap(self.successIcon.pixmap(QSize(48, 48)))
                msgbox.setText('Your new video was successfully created. How would you like to proceed?')
                play = msgbox.addButton('Play video', QMessageBox.AcceptRole)
                play.clicked.connect(self.externalPlayer)
                fileman = msgbox.addButton('Open folder', QMessageBox.AcceptRole)
                fileman.clicked.connect(self.openFolder)
                cont = msgbox.addButton('Continue', QMessageBox.AcceptRole)
                msgbox.setDefaultButton(cont)
                msgbox.setEscapeButton(cont)
                msgbox.exec_()
            return True
        return False

    def joinVideos(self, joinlist, filename):
        listfile = os.path.normpath(os.path.join(os.path.dirname(joinlist[0]), '_cutter.list'))
        fobj = open(listfile, 'w')
        for file in joinlist:
            fobj.write('file \'%s\'\n' % file.replace("'", "\\'"))
        fobj.close()
        ff = FFmpeg(
            executable=self.FFMPEG_bin,
            inputs={listfile: '-f concat -safe 0'},
            outputs={filename: '-c copy -y'}
        )
        try:
            ff.run()
        except:
            print('"Error occurred: %s' % sys.exc_info()[0])
            QMessageBox.critical(self, 'Error Alert', sys.exc_info()[0])
            return
        try:
            os.remove(listfile)
            for file in joinlist:
                if os.path.isfile(file):
                    os.remove(file)
        except:
            pass

    def externalPlayer(self):
        if len(self.finalFilename) and os.path.exists(self.finalFilename):
            if sys.platform == 'win32':
                cmd = 'START /B /I "%s"' % self.finalFilename
            elif sys.platform == 'darwin':
                cmd = 'open "%s"' % self.finalFilename
            else:
                cmd = 'xdg-open "%s"' % self.finalFilename
            proc = self.cmdexec(cmd)
            return proc.returncode

    def openFolder(self):
        if len(self.finalFilename) and os.path.exists(self.finalFilename):
            dirname = os.path.dirname(self.finalFilename)
            if sys.platform == 'win32':
                cmd = 'explorer.exe "%s"' % dirname
            elif sys.platform == 'darwin':
                cmd = 'open "%s"' % dirname
            else:
                cmd = 'xdg-open "%s"' % dirname
            proc = self.cmdexec(cmd)
            return proc.returncode

    def cmdexec(self, cmd, shell=False):
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE, startupinfo=si, env=os.environ, shell=shell)
        else:
            return subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)

    @staticmethod
    def getFilePath():
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.dirname(os.path.realpath(sys.argv[0]))

    def wheelEvent(self, event):
        if self.mediaPlayer.isVideoAvailable() or self.mediaPlayer.isAudioAvailable():
            if event.angleDelta().y() > 0:
                newval = self.positionSlider.value() - 1000
            else:
                newval = self.positionSlider.value() + 1000
            self.positionSlider.setValue(newval)
            self.positionSlider.setSliderPosition(newval)
            self.mediaPlayer.setPosition(newval)
        event.accept()

    def keyPressEvent(self, event):
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
            if addtime != 0:
                newval = self.positionSlider.value() + addtime
                self.positionSlider.setValue(newval)
                self.positionSlider.setSliderPosition(newval)
                self.mediaPlayer.setPosition(newval)
        event.accept()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease and isinstance(obj, VideoSlider):
            if obj.objectName() == 'VideoSlider' and (self.mediaPlayer.isVideoAvailable() or self.mediaPlayer.isAudioAvailable()):
                obj.setValue(QStyle.sliderValueFromPosition(obj.minimum(), obj.maximum(), event.x(), obj.width()))
                self.mediaPlayer.setPosition(obj.sliderPosition())
        return QWidget.eventFilter(self, obj, event)

    def handleError(self):
        self.unsetCursor()
        self.initMediaControls(False)
        print('ERROR: %s' % self.mediaPlayer.errorString())
        QMessageBox.critical(self, 'Error Alert', self.mediaPlayer.errorString())

    def closeEvent(self, event):
        self.parent.closeEvent(event)
