#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shlex
import signal
import subprocess
import sys

from PyQt5.QtCore import QDir, QEvent, QSize, Qt, QTime, QUrl
from PyQt5.QtGui import QFont, QIcon, QPalette, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QHBoxLayout,
                             QLabel, QListWidget, QMainWindow, QMenu,
                             QMessageBox, QSizePolicy, QSlider, QStyle,
                             QToolBar, QToolButton, QVBoxLayout, QWidget, qApp)

from ffmpy import FFmpeg

signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)


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

        self.FFMPEG_bin = 'ffmpeg'
        if sys.platform == 'win32':
            self.FFMPEG_bin = os.path.join(self.getFilePath(), 'bin', 'ffmpeg.exe')

        self.cutTimes = []
        self.timeformat = 'hh:mm:ss'
        self.finalFilename = ''

        self.initIcons()
        self.initActions()
        self.initToolbar()

        sliderQSS = '''QSlider:horizontal {
    margin: 10px 5px;
}

QSlider::groove:horizontal {
    border: 1px solid #999;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
    height: 8px;
    position: absolute;
    left: 2px;
    right: 2px;
    margin: -2px 0;
}

QSlider::sub-page:horizontal {
    border: 1px solid #999;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0083c5, stop:1 #c8dbf9);
    height: 8px;
    position: absolute;
    left: 2px;
    right: 2px;
    margin: -2px 0;
}

QSlider::handle:horizontal {
    background: #FAFAFA;
    border: 1px solid #777;
    width: 18px;
    margin: -3px -2px;
    border-radius: 2px;
}'''

        self.positionSlider = QSlider(Qt.Horizontal, statusTip='Set video frame position', sliderMoved=self.setPosition)
        self.positionSlider.setObjectName('PositionSlider')
        self.positionSlider.setRange(0, 0)
        self.positionSlider.setStyleSheet(sliderQSS)
        self.positionSlider.installEventFilter(self)

        sliderLayout = QHBoxLayout()
        sliderLayout.addWidget(self.positionSlider)

        self.cutlist = QListWidget(customContextMenuRequested=self.itemMenu)
        self.cutlist.setUniformItemSizes(True)
        self.cutlist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cutlist.setFixedWidth(150)
        listfont = QFont('Droid Sans Mono')
        listfont.setStyleHint(QFont.Monospace)
        self.cutlist.setFont(listfont)
        self.cutlist.setStyleSheet('QListView::item { margin-bottom:15px; }')

        self.movieLabel = QLabel('No movie loaded')
        self.movieLabel.setStyleSheet('font-size:16px; font-weight:bold; font-family:sans-serif;')
        self.movieLabel.setAlignment(Qt.AlignCenter)
        self.movieLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.movieLabel.setBackgroundRole(QPalette.Dark)
        self.movieLabel.setAutoFillBackground(True)
        self.movieLoaded = False

        self.videoLayout = QHBoxLayout()
        self.videoLayout.setContentsMargins(0, 0, 0, 0)
        self.videoLayout.addWidget(self.movieLabel)
        self.videoLayout.addWidget(self.cutlist)

        self.timeCounter = QLabel('00:00:00 / 00:00:00')
        timefont = QFont('Droid Sans Mono')
        timefont.setStyleHint(QFont.Monospace)
        self.timeCounter.setFont(timefont)
        self.timeCounter.setStyleSheet('font-size:13px; color:#666; margin-right:150px; margin-bottom:6px;')

        timerLayout = QHBoxLayout()
        timerLayout.addStretch(1)
        timerLayout.addWidget(self.timeCounter)
        timerLayout.addStretch(1)

        self.muteButton = QToolButton(statusTip='Toggle audio mute', clicked=self.muteAudio)
        self.muteButton.setIcon(self.unmuteIcon)
        self.muteButton.setToolTip('Mute')
        self.volumeSlider = QSlider(Qt.Horizontal, statusTip='Adjust volume level', sliderMoved=self.setVolume)
        self.volumeSlider.setToolTip('Volume')
        self.volumeSlider.setValue(50)
        self.volumeSlider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.volumeSlider.setRange(0, 100)

        controlsLayout = QHBoxLayout()
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.lefttoolbar)
        controlsLayout.addWidget(self.centertoolbar)
        controlsLayout.addStretch(1)
        controlsLayout.addWidget(self.muteButton)
        controlsLayout.addWidget(self.volumeSlider)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 4)
        layout.addLayout(self.videoLayout)
        layout.addLayout(timerLayout)
        layout.addLayout(sliderLayout)
        layout.addLayout(controlsLayout)
        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def initIcons(self):
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

    def initActions(self):
        self.openAction = QAction(self.openIcon, 'Open', self, statusTip='Select video', triggered=self.openFile)
        self.playAction = QAction(self.playIcon, 'Play', self, statusTip='Play video', triggered=self.playVideo, enabled=False)
        self.cutStartAction = QAction(self.cutStartIcon, 'Set Start', self, statusTip='Set start marker', triggered=self.cutStart, enabled=False)
        self.cutEndAction = QAction(self.cutEndIcon, 'Set End', self, statusTip='Set end marker', triggered=self.cutEnd, enabled=False)
        self.saveAction = QAction(self.saveIcon, 'Save', self, statusTip='Save new video', triggered=self.cutVideo, enabled=False)
        self.moveItemUpAction = QAction(self.upIcon, 'Move Up', self, statusTip='Move clip up in clip list', triggered=self.moveItemUp, enabled=False)
        self.moveItemDownAction = QAction(self.downIcon, 'Move Down', self, statusTip='Move clip down in clip list', triggered=self.moveItemDown, enabled=False)
        self.removeItemAction = QAction(self.removeIcon, 'Remove clip', self, statusTip='Remove clip from list', triggered=self.removeItem, enabled=False)
        self.removeAllAction = QAction(self.removeAllIcon, 'Remove all', self, statusTip='Remove all clips from list', triggered=self.clearList, enabled=False)

    def initToolbar(self):
        self.lefttoolbar = QToolBar()
        self.lefttoolbar.setStyleSheet('QToolBar QToolButton { min-width:82px; font-size:14px; }')
        self.lefttoolbar.setFloatable(False)
        self.lefttoolbar.setMovable(False)
        self.lefttoolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.lefttoolbar.setIconSize(QSize(24, 24))
        self.lefttoolbar.addAction(self.openAction)
        self.lefttoolbar.addAction(self.playAction)
        self.lefttoolbar.addAction(self.saveAction)
        self.centertoolbar = QToolBar()
        self.centertoolbar.setStyleSheet('QToolBar QToolButton { font-size:14px; }')
        self.centertoolbar.setFloatable(False)
        self.centertoolbar.setMovable(False)
        self.centertoolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.centertoolbar.setIconSize(QSize(24, 24))
        self.centertoolbar.addAction(self.cutStartAction)
        self.centertoolbar.addAction(self.cutEndAction)

    def itemMenu(self, pos):
        globalPos = self.cutlist.mapToGlobal(pos)
        self.cutlistMenu = QMenu()
        self.cutlistMenu.addAction(self.moveItemUpAction)
        self.cutlistMenu.addAction(self.moveItemDownAction)
        self.cutlistMenu.addSeparator()
        self.cutlistMenu.addAction(self.removeItemAction)
        self.cutlistMenu.addAction(self.removeAllAction)
        self.moveItemUpAction.setEnabled(False)
        self.moveItemDownAction.setEnabled(False)
        self.removeItemAction.setEnabled(False)
        self.removeAllAction.setEnabled(False)
        index = self.cutlist.currentRow()
        if index != -1:
            if index > 0:
                self.moveItemUpAction.setEnabled(True)
            if index < self.cutlist.count()-1:
                self.moveItemDownAction.setEnabled(True)
            if self.cutlist.count() > 0:
                self.removeItemAction.setEnabled(True)
                self.removeAllAction.setEnabled(True)
        self.cutlistMenu.exec_(globalPos)

    def moveItemUp(self):
        index = self.cutlist.currentRow()
        tmpItem = self.cutTimes[index]
        del self.cutTimes[index]
        self.cutTimes.insert(index-1, tmpItem)
        self.renderTimes()

    def moveItemDown(self):
        index = self.cutlist.currentRow()
        tmpItem = self.cutTimes[index]
        del self.cutTimes[index]
        self.cutTimes.insert(index+1, tmpItem)
        self.renderTimes()

    def removeItem(self):
        index = self.cutlist.currentRow()
        del self.cutTimes[index]
        self.renderTimes()
        self.initMediaControls()
        if len(self.cutTimes) > 0:
            self.saveAction.setEnabled(True)

    def clearList(self):
        self.cutTimes.clear()
        self.cutlist.clear()
        self.initMediaControls()

    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(parent=self.parent, caption='Select video', directory=QDir.homePath())
        if filename != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.initMediaControls(True)
            self.cutlist.clear()
            self.cutTimes = []
            self.parent.setWindowTitle('VideoCutter - %s' % os.path.basename(filename))
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
            if self.mediaPlayer.state() == QMediaPlayer.StoppedState:
                self.mediaPlayer.play()
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
        self.renderTimes()

    def cutEnd(self):
        item = self.cutTimes[len(self.cutTimes) - 1]
        selected = self.deltaToQTime(self.mediaPlayer.position())
        if selected.__lt__(item[0]):
            QMessageBox.critical(self, 'Invalid END Time', 'The clip end time must come AFTER it\'s start time. Please try again.')
            return
        item.append(selected)
        self.cutStartAction.setEnabled(True)
        self.cutEndAction.setDisabled(True)
        self.renderTimes()

    def renderTimes(self):
        self.cutlist.clear()
        for item in self.cutTimes:
            endItem = ''
            if len(item) == 2:
                endItem = item[1].toString(self.timeformat)
            self.cutlist.addItem('START => %s\n  END => %s' % (item[0].toString(self.timeformat), endItem))
        if len(self.cutTimes):
            self.saveAction.setEnabled(True)
        if len(self.cutTimes) == 0 or len(self.cutTimes[0]) != 2:
            self.saveAction.setEnabled(False)

    @staticmethod
    def deltaToQTime(millisecs):
        secs = millisecs / 1000
        return QTime((secs / 3600) % 60, (secs / 60) % 60, secs % 60, (secs * 1000) % 1000)

    def cutVideo(self):
        self.setCursor(Qt.BusyCursor)
        filename = ''
        filelist = []
        source = self.mediaPlayer.currentMedia().canonicalUrl().toLocalFile()
        _, sourceext = os.path.splitext(source)
        if len(self.cutTimes):
            self.finalFilename, _ = QFileDialog.getSaveFileName(parent=self, caption='Save video', directory=source,
                                                                filter='Video files (*%s)' % sourceext)
            if self.finalFilename != '':
                file, ext = os.path.splitext(self.finalFilename)
                index = 1
                for clip in self.cutTimes:
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
                cmd = self.finalFilename
            else:
                cmd = 'xdg-open %s' % self.finalFilename
            returncode = self.cmdexec(cmd)

    def openFolder(self):
        if len(self.finalFilename) and os.path.exists(self.finalFilename):
            dirname = os.path.dirname(self.finalFilename)
            if sys.platform == 'win32':
                cmd = 'C:\\Windows\\explorer.exe %s' % dirname
            elif sys.platform == 'darwin':
                cmd = 'open %s' % dirname
            else:
                cmd = 'xdg-open %s' % dirname
            returncode = self.cmdexec(cmd)

    def cmdexec(self, cmd):
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, startupinfo=si, env=os.environ, shell=False)
        else:
            return subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)    

    @staticmethod
    def getFilePath():
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.dirname(os.path.realpath(sys.argv[0]))

    def eventFilter(self, object, event):
        if event.type() == QEvent.MouseButtonRelease and isinstance(object, QSlider):
            if object.objectName() == 'PositionSlider' and (self.mediaPlayer.isVideoAvailable() or self.mediaPlayer.isAudioAvailable()):
                object.setValue(QStyle.sliderValueFromPosition(object.minimum(), object.maximum(), event.x(), object.width()))
                self.mediaPlayer.setPosition(object.sliderPosition())
        return QWidget.eventFilter(self, object, event)

    def handleError(self):
        self.unsetCursor()
        self.initMediaControls(False)
        print('ERROR: %s' % self.mediaPlayer.errorString())
        QMessageBox.critical(self, 'Error Alert', self.mediaPlayer.errorString())

    def closeEvent(self, event):
        self.parent.closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, parent=None, flags=Qt.Window):
        super(MainWindow, self).__init__(parent, flags)
        self.statusBar().showMessage('Ready')
        self.setWindowTitle('VideoCutter')
        self.setWindowIcon(QIcon(os.path.join(VideoCutter.getFilePath(), 'icons', 'videocutter.png')))
        self.cutter = VideoCutter(self)
        self.setCentralWidget(self.cutter)
        self.resize(800, 600)

    def closeEvent(self, event):
        self.cutter.deleteLater()
        self.deleteLater()
        qApp.quit()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
