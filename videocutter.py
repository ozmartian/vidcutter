    #!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import QDir, Qt, QUrl, QFile, QFileInfo, QSize
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAction, QAbstractItemView, QApplication, QFileDialog, QHBoxLayout, QMainWindow,
                             QSizePolicy, QSlider, QStyle, QStyleFactory, QListWidget, QListWidgetItem,
                             QToolBar, QToolButton, QVBoxLayout, QWidget, qApp)


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

        self.initIcons()
        self.initActions()
        self.initToolbar()

        # MainWindow.loadStyleSheet(filepath=os.path.join(self.rootPath, 'qss', 'qslider.qss'))

        self.positionSlider = QSlider(Qt.Horizontal, sliderMoved=self.setPosition)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.setStyleSheet('margin:8px 5px;')

        self.zonelist = QListWidget()
        self.zonelist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.zonelist.setFixedWidth(200)
        listItem = QListWidgetItem("START => 00:04:35.000\nEND => 00:04:35.000")
        listItem.setSizeHint(QSize(0, 50))
        self.zonelist.addItem(listItem)

        videoLayout = QHBoxLayout()
        videoLayout.setContentsMargins(0, 0, 0, 0)
        videoLayout.addWidget(self.videoWidget)
        videoLayout.addWidget(self.zonelist)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addLayout(videoLayout)
        layout.addWidget(self.positionSlider)

        self.muteButton = QToolButton(clicked=self.muteAudio)
        self.muteButton.setIcon(self.unmuteIcon)
        self.volumeSlider = QSlider(Qt.Horizontal, sliderMoved=self.setVolume)
        self.volumeSlider.setFixedWidth(100)
        self.volumeSlider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.volumeSlider.setRange(0, 100)

        controlsLayout = QHBoxLayout()
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.toolbar)
        controlsLayout.addStretch(1)
        controlsLayout.addSpacing(10)
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
        self.fscreenIcon = QIcon(os.path.join(self.rootPath, 'icons', 'fullscreen.png'))
        self.muteIcon = QIcon(os.path.join(self.rootPath, 'icons', 'muted.png'))
        self.unmuteIcon = QIcon(os.path.join(self.rootPath, 'icons', 'unmuted.png'))

    def initActions(self):
        self.openAction = QAction(self.openIcon, 'Open', self, statusTip='Select video', triggered=self.openFile)
        self.playAction = QAction(self.playIcon, 'Play', self, statusTip='Play video', triggered=self.playVideo,
                                  enabled=False)
        self.cutStartAction = QAction(self.cutStartIcon, 'Start', self, statusTip='Mark start of clip',
                                       triggered=self.cutStart, enabled=False)
        self.cutEndAction = QAction(self.cutEndIcon, 'End', self, statusTip='Mark end of clip',
                                     triggered=self.cutEnd, enabled=False)
        self.saveAction = QAction(self.saveIcon, 'Save', self, statusTip='Save cuts to video file',
                                  triggered=self.saveVideo, enabled=False)
        self.fscreenAction = QAction(self.fscreenIcon, 'Fullscreen', self, statusTip='View in fullscreen mode',
                                        triggered=self.toggleFullscreen, enabled=False)

    def initToolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toolbar.setIconSize(QSize(26, 26))
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.playAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.cutStartAction)
        self.toolbar.addAction(self.cutEndAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.fscreenAction)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(parent=self.parent, caption='Select video', directory=QDir.homePath())
        if fileName != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.enableMediaControls(True)

    def playVideo(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def enableMediaControls(self, flag=True):
        self.playAction.setEnabled(flag)
        self.cutStartAction.setEnabled(flag)
        self.cutEndAction.setEnabled(flag)
        self.fscreenAction.setEnabled(flag)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def mediaStateChanged(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playAction.setIcon(self.pauseIcon)
            self.playAction.setText('Pause')
        else:
            self.playAction.setIcon(self.playIcon)
            self.playAction.setText('Play ')

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
        pass

    def cutEnd(self):
        pass

    def saveVideo(self):
        pass

    def handleError(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self, parent=None, flags=Qt.Window):
        super(MainWindow, self).__init__(parent, flags)
        self.statusBar().showMessage('Ready')
        self.setCentralWidget(VideoCutter(self))
        self.setWindowTitle('VideoCutter')
        self.setWindowIcon(QIcon(os.path.join(QFileInfo(__file__).absolutePath(), 'icons', 'app.png')))
        self.resize(800, 600)

    @staticmethod
    def loadStyleSheet(filepath=None, stylesheet=None):
        if filepath is not None:
            stylefile = QFile(filepath)
            stylefile.open(QFile.ReadOnly)
            stylesheet = str(stylefile.readAll(), encoding='utf8')
        if stylesheet is not None:
            qApp.setStyleSheet(stylesheet)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
