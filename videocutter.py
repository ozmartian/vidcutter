#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import QDir, Qt, QUrl, QFile, QFileInfo, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAction, QAbstractItemView, QApplication, QFileDialog, QHBoxLayout, QMainWindow,
                             QPushButton, QSizePolicy, QSlider, QStyle, QStyleFactory, QStyleOptionButton, QTableWidget,
                             QTableWidgetItem, QToolBar, QVBoxLayout, QWidget, qApp)


class VideoCutter(QWidget):
    def __init__(self, parent):
        super(VideoCutter, self).__init__(parent)
        self.parent = parent
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.videoWidget = QVideoWidget()

        self.rootPath = QFileInfo(__file__).absolutePath()

        self.openIcon = QIcon(os.path.join(self.rootPath, 'icons', 'open.png'))
        self.playIcon = QIcon(os.path.join(self.rootPath, 'icons', 'play.png'))
        self.pauseIcon = QIcon(os.path.join(self.rootPath, 'icons', 'pause.png'))
        self.markStartIcon = QIcon(os.path.join(self.rootPath, 'icons', 'start.png'))
        self.markEndIcon = QIcon(os.path.join(self.rootPath, 'icons', 'end.png'))

        self.initActions()
        self.initToolbar()

        # MainWindow.loadStyleSheet(os.path.join(self.rootPath, 'qss', 'qslider.qss'))

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setStyle(QStyleFactory.create('Oxygen'))
        self.positionSlider.setRange(0, 1000)
        # self.positionSlider.setTickPosition(QSlider.TicksBelow)
        # self.positionSlider.setTickInterval(5)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        # self.errorLabel = QLabel()
        # self.errorLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.timelist = QTableWidget()
        self.timelist.setFixedWidth(200)
        self.timelist.horizontalScrollBar().setVisible(False)
        self.timelist.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.timelist.setColumnCount(2)
        self.timelist.setRowCount(2)
        self.timelist.verticalHeader().setVisible(False)
        self.timelist.setHorizontalHeaderLabels(['Position', 'Time'])
        self.timelist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.timelist.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.timelist.setSelectionMode(QAbstractItemView.MultiSelection)
        self.timelist.setItem(0, 0, QTableWidgetItem('start'))
        self.timelist.setItem(0, 1, QTableWidgetItem('00:04:03'))
        self.timelist.setItem(1, 0, QTableWidgetItem('end'))
        self.timelist.setItem(1, 1, QTableWidgetItem('00:12:42'))

        videoLayout = QHBoxLayout()
        videoLayout.setContentsMargins(0, 0, 0, 0)
        videoLayout.addWidget(self.videoWidget)
        videoLayout.addWidget(self.timelist)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(videoLayout)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.positionSlider)
        # layout.addWidget(self.errorLabel)

        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def initActions(self):
        self.openAction = QAction(self.openIcon, 'Open', self, statusTip='Select video', triggered=self.openFile)
        self.playAction = QAction(self.playIcon, 'Play', self, statusTip='Play video', triggered=self.playVideo,
                                  enabled=False)
        self.markStartAction = QAction(self.markStartIcon, 'Mark Start', self, statusTip='Mark start of clip',
                                       triggered=self.markStart, enabled=False)
        self.markEndAction = QAction(self.markEndIcon, 'Mark End', self, statusTip='Mark end of clip',
                                     triggered=self.markEnd, enabled=False)

    def initToolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.addAction(self.openAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.playAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.markStartAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.markEndAction)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(parent=self.parent, caption='Select video', directory=QDir.homePath())
        if fileName != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playAction.setEnabled(True)
            self.markStartAction.setEnabled(True)

    def playVideo(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

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
            self.playAction.setText('Play')

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def markStart(self):
        pass

    def markEnd(self):
        pass

    def handleError(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self, parent=None, flags=Qt.Window):
        super(MainWindow, self).__init__(parent, flags)
        self.cutter = VideoCutter(self)
        self.statusBar()
        self.setCentralWidget(self.cutter)
        self.setWindowTitle('VideoCutter')
        self.setWindowIcon(QIcon(os.path.join(QFileInfo(__file__).absolutePath(), 'icons', 'app.png')))
        self.resize(800, 600)

    @staticmethod
    def loadStyleSheet(sheetFile):
        file = QFile(sheetFile)
        file.open(QFile.ReadOnly)
        styleSheet = str(file.readAll(), encoding='utf8')
        qApp.setStyleSheet(styleSheet)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
