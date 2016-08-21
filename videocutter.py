#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import QDir, QFileInfo, QSize, Qt, QTime, QUrl
from PyQt5.QtGui import QFont, QIcon, QPalette
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QHBoxLayout,
                             QLabel, QListWidget, QMainWindow, QSizePolicy, QSlider, QToolBar,
                             QToolButton, QVBoxLayout, QWidget, qApp)
from ffmpy import FFmpeg


class VideoWidget(QVideoWidget):
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        p = self.palette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)
        self.setAttribute(Qt.WA_OpaquePaintEvent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.setFullScreen(False)
            event.accept()
        elif event.key() == Qt.Key_Enter and not self.isFullScreen():
            self.setFullScreen(not self.isFullScreen())
            event.accept()
        else:
            super(VideoWidget, self).keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.setFullScreen(not self.isFullScreen())
        event.accept()


class VideoCutter(QWidget):
    def __init__(self, parent):
        super(VideoCutter, self).__init__(parent)
        self.parent = parent
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videoWidget = VideoWidget()
        self.rootPath = QFileInfo(__file__).absolutePath()

        self.cutTimes = []
        self.cutResults = []
        self.timeformat = 'hh:mm:ss'

        self.initIcons()
        self.initActions()
        self.initToolbar()

        self.positionSlider = QSlider(Qt.Horizontal, statusTip='Set video frame position', sliderMoved=self.setPosition)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.setStyleSheet('margin:8px 5px;')

        sliderLayout = QHBoxLayout()
        sliderLayout.addWidget(self.positionSlider)

        self.cutlist = QListWidget()
        self.cutlist.setUniformItemSizes(True)
        self.cutlist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cutlist.setFixedWidth(150)
        listfont = QFont('Droid Sans Mono')
        listfont.setStyleHint(QFont.Monospace)
        self.cutlist.setFont(listfont)
        self.cutlist.setStyleSheet('QListView::item { margin-bottom:15px; }')

        self.movieLabel = QLabel('No movie loaded')
        self.movieLabel.setAlignment(Qt.AlignCenter)
        self.movieLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.movieLabel.setBackgroundRole(QPalette.Dark)
        self.movieLabel.setAutoFillBackground(True)
        self.movieLoaded = False

        self.videoLayout = QHBoxLayout()
        self.videoLayout.setContentsMargins(0, 0, 0, 0)
        self.videoLayout.addWidget(self.movieLabel)
        self.videoLayout.addWidget(self.cutlist)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addLayout(self.videoLayout)
        layout.addLayout(sliderLayout)

        self.timeCounter = QLabel('00:00:00 / 00:00:00')
        timefont = QFont('Droid Sans Mono')
        timefont.setStyleHint(QFont.Monospace)
        self.timeCounter.setFont(timefont)
        self.timeCounter.setStyleSheet('color:#666; margin-right:6px;')
        self.parent.statusBar().addPermanentWidget(self.timeCounter)

        self.muteButton = QToolButton(statusTip='Toggle audio mute', clicked=self.muteAudio)
        self.muteButton.setIcon(self.unmuteIcon)
        self.muteButton.setToolTip('Mute')
        self.volumeSlider = QSlider(Qt.Horizontal, statusTip='Adjust volume level', sliderMoved=self.setVolume)
        self.volumeSlider.setToolTip('Volume')
        self.volumeSlider.setValue(50)
        # self.volumeSlider.setFixedWidth(100)
        self.volumeSlider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.volumeSlider.setRange(0, 100)

        controlsLayout = QHBoxLayout()
        controlsLayout.addWidget(self.lefttoolbar)
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.centertoolbar)
        controlsLayout.addStretch(1)
        # controlsLayout.addWidget(self.timeCounter)
        controlsLayout.addWidget(self.muteButton)
        controlsLayout.addWidget(self.volumeSlider)

        layout.addLayout(controlsLayout)
        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def initIcons(self):
        self.openIcon = QIcon(os.path.join(self.rootPath, 'icons', 'open.png'))
        self.playIcon = QIcon(os.path.join(self.rootPath, 'icons', 'play.png'))
        self.pauseIcon = QIcon(os.path.join(self.rootPath, 'icons', 'pause.png'))
        self.cutStartIcon = QIcon(os.path.join(self.rootPath, 'icons', 'start.png'))
        self.cutEndIcon = QIcon(os.path.join(self.rootPath, 'icons', 'end.png'))
        self.saveIcon = QIcon(os.path.join(self.rootPath, 'icons', 'save.png'))
        self.muteIcon = QIcon(os.path.join(self.rootPath, 'icons', 'muted.png'))
        self.unmuteIcon = QIcon(os.path.join(self.rootPath, 'icons', 'unmuted.png'))

    def initActions(self):
        self.openAction = QAction(self.openIcon, 'Open', self, statusTip='Select video', triggered=self.openFile)
        self.playAction = QAction(self.playIcon, 'Play', self, statusTip='Play video', triggered=self.playVideo, enabled=False)
        self.cutStartAction = QAction(self.cutStartIcon, 'Set Start', self, statusTip='Set start marker', triggered=self.cutStart, enabled=False)
        self.cutEndAction = QAction(self.cutEndIcon, 'Set End', self, statusTip='Set end marker', triggered=self.cutEnd, enabled=False)
        self.saveAction = QAction(self.saveIcon, 'Save', self, statusTip='Add clip to cutting list', triggered=self.saveVideo, enabled=False)

    def initToolbar(self):
        self.lefttoolbar = QToolBar()
        self.lefttoolbar.setStyleSheet('QToolBar QToolButton { min-width:82px; }')
        self.lefttoolbar.setFloatable(False)
        self.lefttoolbar.setMovable(False)
        self.lefttoolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.lefttoolbar.setIconSize(QSize(24, 24))
        self.lefttoolbar.addAction(self.openAction)
        self.lefttoolbar.addAction(self.playAction)
        self.lefttoolbar.addAction(self.saveAction)
        self.centertoolbar = QToolBar()
        self.centertoolbar.setFloatable(False)
        self.centertoolbar.setMovable(False)
        self.centertoolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.centertoolbar.setIconSize(QSize(24, 24))
        self.centertoolbar.addAction(self.cutStartAction)
        self.centertoolbar.addAction(self.cutEndAction)

    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(parent=self.parent, caption='Select video', directory=QDir.homePath())
        if filename != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.initMediaControls(True)
            self.cutlist.clear()
            self.cutTimes = []
            if not self.movieLoaded:
                self.videoLayout.replaceWidget(self.movieLabel, self.videoWidget)
                self.movieLabel.deleteLater()
                self.movieLoaded = True

    def playVideo(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def initMediaControls(self, flag=True):
        self.playAction.setEnabled(flag)
        self.cutStartAction.setEnabled(flag)
        self.cutEndAction.setEnabled(False)
        self.saveAction.setEnabled(False)

    def setPosition(self, position):
        if self.mediaPlayer.isVideoAvailable():
            self.mediaPlayer.pause()
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
        else:
            self.mediaPlayer.setMuted(not self.mediaPlayer.isMuted())
            self.muteButton.setIcon(self.muteIcon)

    def setVolume(self, volume):
        self.mediaPlayer.setVolume(volume)

    def toggleFullscreen(self):
        self.videoWidget.setFullScreen(not self.videoWidget.isFullScreen())

    def cutStart(self):
        self.cutTimes.append([self.deltaToQTime(self.mediaPlayer.position())])
        self.cutStartAction.setDisabled(True)
        self.cutEndAction.setEnabled(True)

    def cutEnd(self):
        self.cutTimes[len(self.cutTimes)-1].append(self.deltaToQTime(self.mediaPlayer.position()))
        self.cutStartAction.setEnabled(True)
        self.cutEndAction.setDisabled(True)
        self.renderTimes()

    def renderTimes(self):
        self.cutlist.clear()
        for item in self.cutTimes:
            self.cutlist.addItem('START => ' + item[0].toString(self.timeformat) + '\n  END => ' + item[1].toString(self.timeformat))
        if len(self.cutTimes):
            self.saveAction.setEnabled(True)

    @staticmethod
    def deltaToQTime(millisecs):
        secs = millisecs / 1000
        return QTime((secs / 3600) % 60, (secs / 60) % 60, secs % 60, (secs * 1000) % 1000)

    def saveVideo(self):
        if not len(self.cutTimes):
            return
        self.cutResults.clear()
        for item in self.cutTimes:
            self.cutResults.append(self.cutVideo(item[0], item[1]))

    def cutVideo(self, start: QTime, end: QTime):
        source = self.mediaPlayer.currentMedia().canonicalUrl().path()
        target = source # '%s_NEW%s' % os.path.splitext(source)
        cliplen = self.deltaToQTime(start.msecsTo(end)).toString(self.timeformat)
        filename, _ = QFileDialog.getSaveFileName(parent=self.parent, caption='Save video', directory=os.path.dirname(source))
        if filename != '':
            ff = FFmpeg(
                inputs={source: None},
                outputs={target: '-ss %s -t %s -vcodec copy -acodec copy -y' % (start.toString(self.timeformat), cliplen)}
            )
            return ff.run()
        return

    def handleError(self):
        self.initMediaControls(False)
        print('ERROR: %s' % self.mediaPlayer.errorString())

    def closeEvent(self, event):
        self.parent.closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, parent=None, flags=Qt.Window):
        super(MainWindow, self).__init__(parent, flags)
        self.statusBar().showMessage('Ready')
        self.cutter = VideoCutter(self)
        self.setCentralWidget(self.cutter)
        self.setWindowTitle('VideoCutter')
        self.setWindowIcon(QIcon(os.path.join(QFileInfo(__file__).absolutePath(), 'icons', 'videocutter.png')))
        self.resize(800, 600)

    def closeEvent(self, event):
        self.cutter.deleteLater()
        self.deleteLater()
        qApp.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
