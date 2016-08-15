#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import QDir, Qt, QUrl, QFileInfo, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAction, QAbstractItemView, QApplication, QFileDialog, QHBoxLayout, QMainWindow,
                             QPushButton, QSizePolicy, QSlider, QTableWidget, QTableWidgetItem, QToolBar,
                             QVBoxLayout, QWidget)


class VideoCutter(QWidget):
    def __init__(self, parent):
        super(VideoCutter, self).__init__(parent)
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.videoWidget = QVideoWidget()

        root = QFileInfo(__file__).absolutePath()
        self.playIcon = QIcon(os.path.join(root, 'icons', 'play.png'))
        self.pauseIcon = QIcon(os.path.join(root, 'icons', 'pause.png'))

        self.playButton = QPushButton()
        self.playButton.setIconSize(QSize(24, 24))
        self.playButton.setToolTip("Play")
        self.playButton.setStatusTip("Play video")
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.playIcon)
        self.playButton.clicked.connect(self.playVideo)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 100)
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
        self.timelist.setRowCount(1)
        self.timelist.verticalHeader().setVisible(False)
        self.timelist.setHorizontalHeaderLabels(['Type', 'Position'])
        self.timelist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.timelist.setSelectionMode(QAbstractItemView.SingleSelection)
        self.timelist.setItem(0, 1, QTableWidgetItem("test"))

        videoLayout = QHBoxLayout()
        videoLayout.setContentsMargins(0, 0, 0, 0)
        videoLayout.addWidget(self.videoWidget)
        videoLayout.addWidget(self.timelist)

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(10, 10, 10, 10)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)

        layout = QVBoxLayout()
        layout.addLayout(videoLayout)
        layout.addLayout(controlLayout)
        # layout.addWidget(self.errorLabel)

        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def playVideo(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
            self.playButton.setIcon(self.playIcon)
        else:
            self.mediaPlayer.play()
            self.playButton.setIcon(self.pauseIcon)

    def setPosition(self):
        pass

    def mediaStateChanged(self):
        pass

    def positionChanged(self):
        pass

    def durationChanged(self):
        pass

    def handleError(self):
        pass


class MainWindow(QMainWindow):
    cutter = VideoCutter

    def __init__(self, parent=None, flags=Qt.Window):
        super(MainWindow, self).__init__(parent, flags)
        self.createActions()
        self.initToolbar()
        self.createStatusBar()
        self.cutter = VideoCutter(self)
        self.setCentralWidget(self.cutter)
        self.setWindowTitle("VideoCutter")
        self.resize(800, 600)

    def createActions(self):
        root = QFileInfo(__file__).absolutePath()
        self.openAction = QAction(QIcon(os.path.join(root, "icons", "open.png")), "Open", self)
        self.openAction.setStatusTip("Open an existing file")
        self.openAction.triggered.connect(self.openFile)

    def initToolbar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.addAction(self.openAction)
        self.addToolBar(self.toolbar)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(parent=self, caption="Select video", directory=QDir.homePath())
        if fileName != '':
            self.cutter.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.cutter.playButton.setEnabled(True)

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
