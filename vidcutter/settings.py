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

import os
import sys

from PyQt5.QtCore import pyqtSlot, QDir, QSize, Qt
from PyQt5.QtGui import QCloseEvent, QColor, QIcon, QPainter, QPen, QPixmap, QShowEvent
from PyQt5.QtWidgets import (qApp, QButtonGroup, QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
                             QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget,
                             QListWidgetItem, QMessageBox, QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
                             QStackedWidget, QStyleFactory, QVBoxLayout, QWidget)

from vidcutter.libs.videoservice import VideoService


class LogsPage(QWidget):
    def __init__(self, parent=None):
        super(LogsPage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingslogspage')
        verboseCheckbox = QCheckBox('Enable verbose logging', self)
        verboseCheckbox.setToolTip('Detailed log ouput to log file and console')
        verboseCheckbox.setCursor(Qt.PointingHandCursor)
        verboseCheckbox.setChecked(self.parent.parent.parent.verboseLogs)
        verboseCheckbox.stateChanged.connect(self.setVerboseLogs)
        verboseLabel = QLabel('''
            <b>ON:</b> includes detailed logs from video player (MPV) and backend services
            <br/>
            <b>OFF:</b> includes errors and important messages to log and console
        ''', self)
        verboseLabel.setObjectName('verboselogslabel')
        verboseLabel.setTextFormat(Qt.RichText)
        verboseLabel.setWordWrap(True)
        logsLayout = QVBoxLayout()
        logsLayout.addWidget(verboseCheckbox)
        logsLayout.addWidget(verboseLabel)
        logsGroup = QGroupBox('Logging')
        logsGroup.setLayout(logsLayout)
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(15)
        mainLayout.addWidget(logsGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    def setVerboseLogs(self, state: int) -> None:
        self.parent.parent.saveSetting('verboseLogs', state == Qt.Checked)
        self.parent.parent.parent.verboseLogs = (state == Qt.Checked)


class ThemePage(QWidget):
    def __init__(self, parent=None):
        super(ThemePage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingsthemepage')
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(15)
        pen = QPen(QColor('#4D5355' if self.parent.theme == 'dark' else '#B9B9B9'))
        pen.setWidth(2)
        theme_light = QPixmap(':/images/theme-light.png', 'PNG')
        painter = QPainter(theme_light)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, theme_light.width(), theme_light.height())
        theme_dark = QPixmap(':/images/theme-dark.png', 'PNG')
        painter = QPainter(theme_dark)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, theme_dark.width(), theme_dark.height())
        self.lightRadio = QRadioButton(self)
        self.lightRadio.setIcon(QIcon(theme_light))
        self.lightRadio.setIconSize(QSize(165, 121))
        self.lightRadio.setCursor(Qt.PointingHandCursor)
        self.lightRadio.clicked.connect(self.switchTheme)
        self.lightRadio.setChecked(self.parent.theme == 'light')
        self.darkRadio = QRadioButton(self)
        self.darkRadio.setIcon(QIcon(theme_dark))
        self.darkRadio.setIconSize(QSize(165, 121))
        self.darkRadio.setCursor(Qt.PointingHandCursor)
        self.darkRadio.clicked.connect(self.switchTheme)
        self.darkRadio.setChecked(self.parent.theme == 'dark')
        themeLayout = QGridLayout()
        themeLayout.setColumnStretch(0, 1)
        themeLayout.addWidget(self.lightRadio, 0, 1)
        themeLayout.addWidget(self.darkRadio, 0, 3)
        themeLayout.addWidget(QLabel('Light', self), 1, 1, Qt.AlignHCenter)
        themeLayout.setColumnStretch(2, 1)
        themeLayout.addWidget(QLabel('Dark', self), 1, 3, Qt.AlignHCenter)
        themeLayout.setColumnStretch(4, 1)
        themeGroup = QGroupBox('Theme')
        themeGroup.setLayout(themeLayout)
        mainLayout.addWidget(themeGroup)
        index_leftRadio = QRadioButton('Clips on left')
        index_leftRadio.setToolTip('Display Clip Index on the left hand side')
        index_leftRadio.setCursor(Qt.PointingHandCursor)
        index_leftRadio.setChecked(self.parent.parent.indexLayout == 'left')
        index_rightRadio = QRadioButton('Clips on right')
        index_rightRadio.setToolTip('Display Clip Index on the right hand side')
        index_rightRadio.setCursor(Qt.PointingHandCursor)
        index_rightRadio.setChecked(self.parent.parent.indexLayout == 'right')
        index_buttonGroup = QButtonGroup(self)
        index_buttonGroup.addButton(index_leftRadio, 1)
        index_buttonGroup.addButton(index_rightRadio, 2)
        # noinspection PyUnresolvedReferences
        index_buttonGroup.buttonClicked[int].connect(self.parent.parent.setClipIndexLayout)
        indexLayout = QHBoxLayout()
        indexLayout.addWidget(index_leftRadio)
        indexLayout.addWidget(index_rightRadio)
        layoutGroup = QGroupBox('Layout')
        layoutGroup.setLayout(indexLayout)
        mainLayout.addWidget(layoutGroup)
        toolbar_labels = self.parent.settings.value('toolbarLabels', 'beside', type=str)
        toolbar_notextRadio = QRadioButton('No text (buttons only)', self)
        toolbar_notextRadio.setToolTip('No text (buttons only)')
        toolbar_notextRadio.setCursor(Qt.PointingHandCursor)
        toolbar_notextRadio.setChecked(toolbar_labels == 'none')
        toolbar_underRadio = QRadioButton('Text under buttons', self)
        toolbar_underRadio.setToolTip('Text under buttons')
        toolbar_underRadio.setCursor(Qt.PointingHandCursor)
        toolbar_underRadio.setChecked(toolbar_labels == 'under')
        toolbar_besideRadio = QRadioButton('Text beside buttons', self)
        toolbar_besideRadio.setToolTip('Text beside buttons')
        toolbar_besideRadio.setCursor(Qt.PointingHandCursor)
        toolbar_besideRadio.setChecked(toolbar_labels == 'beside')
        toolbar_buttonGroup = QButtonGroup(self)
        toolbar_buttonGroup.addButton(toolbar_besideRadio, 1)
        toolbar_buttonGroup.addButton(toolbar_underRadio, 2)
        toolbar_buttonGroup.addButton(toolbar_notextRadio, 3)
        # noinspection PyUnresolvedReferences
        toolbar_buttonGroup.buttonClicked[int].connect(self.setLabelStyle)
        toolbarLayout = QGridLayout()
        toolbarLayout.addWidget(toolbar_besideRadio, 0, 0)
        toolbarLayout.addWidget(toolbar_underRadio, 0, 1)
        toolbarLayout.addWidget(toolbar_notextRadio, 1, 0)
        toolbarGroup = QGroupBox('Toolbar')
        toolbarGroup.setLayout(toolbarLayout)
        mainLayout.addWidget(toolbarGroup)
        nativeDialogsCheckbox = QCheckBox('Use native dialogs', self)
        nativeDialogsCheckbox.setToolTip('Use native file dialogs')
        nativeDialogsCheckbox.setCursor(Qt.PointingHandCursor)
        nativeDialogsCheckbox.setChecked(self.parent.parent.nativeDialogs)
        nativeDialogsCheckbox.stateChanged.connect(self.setNativeDialogs)
        nativeDialogsLabel = QLabel('''
            <b>ON:</b> use native dialog widgets as provided by your operating system
            <br/>
            <b>OFF:</b> use a generic file open & save dialog widget provided by the Qt toolkit
            <br/><br/>
            <b>NOTE:</b> native dialogs should always be used if working
        ''', self)
        nativeDialogsLabel.setObjectName('nativedialogslabel')
        nativeDialogsLabel.setTextFormat(Qt.RichText)
        nativeDialogsLabel.setWordWrap(True)
        advancedLayout = QVBoxLayout()
        advancedLayout.addWidget(nativeDialogsCheckbox)
        advancedLayout.addWidget(nativeDialogsLabel)
        advancedGroup = QGroupBox('Advanced')
        advancedGroup.setLayout(advancedLayout)
        mainLayout.addWidget(advancedGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    @pyqtSlot(int)
    def setLabelStyle(self, button_id: int) -> None:
        if button_id == 2:
            style = 'under'
        elif button_id == 3:
            style = 'none'
        else:
            style = 'beside'
        self.parent.settings.setValue('toolbarLabels', style)
        self.parent.parent.setToolBarStyle(style)

    @pyqtSlot(int)
    def setNativeDialogs(self, state: int) -> None:
        self.parent.parent.saveSetting('nativeDialogs', state == Qt.Checked)
        self.parent.parent.nativeDialogs = (state == Qt.Checked)

    @pyqtSlot(bool)
    def switchTheme(self) -> None:
        if self.darkRadio.isChecked():
            newtheme = 'dark'
        else:
            newtheme = 'light'
        if newtheme != self.parent.theme:
            # noinspection PyArgumentList
            mbox = QMessageBox(icon=QMessageBox.NoIcon, windowTitle='Restart required', minimumWidth=500,
                               textFormat=Qt.RichText, objectName='genericdialog')
            mbox.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
            mbox.setText('''
                <style>
                    h1 {
                        color: %s;
                        font-family: "Futura LT", sans-serif;
                        font-weight: normal;
                    }
                </style>
                <h1>Warning</h1>
                <p>The application needs to be restarted in order to switch themes. Attempts will be made to reopen
                media files and add back all clip times from your clip index.</p>
                <p>Would you like to restart and switch themes now?</p>'''
                         % ('#C681D5' if self.parent.theme == 'dark' else '#642C68'))
            mbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            mbox.setDefaultButton(QMessageBox.Yes)
            response = mbox.exec_()
            if response == QMessageBox.Yes:
                self.parent.settings.setValue('theme', newtheme)
                self.parent.parent.theme = newtheme
                self.parent.parent.parent.reboot()
            else:
                self.darkRadio.setChecked(True) if newtheme == 'light' else self.lightRadio.setChecked(True)


class VideoPage(QWidget):
    def __init__(self, parent=None):
        super(VideoPage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingsvideopage')
        decodingCheckbox = QCheckBox('Hardware decoding', self)
        decodingCheckbox.setToolTip('Enable hardware based video decoding')
        decodingCheckbox.setCursor(Qt.PointingHandCursor)
        decodingCheckbox.setChecked(self.parent.parent.hardwareDecoding)
        decodingCheckbox.stateChanged.connect(self.switchDecoding)
        decodingLabel = QLabel('''
            <b>ON:</b> saves laptop power + prevents video tearing; falls back to software decoding if your hardware is
            not supported
            <br/>
            <b>OFF:</b> always use software based decoding''', self)
        decodingLabel.setObjectName('decodinglabel')
        decodingLabel.setTextFormat(Qt.RichText)
        decodingLabel.setWordWrap(True)
        pboCheckbox = QCheckBox('Enable use of PBOs', self)
        pboCheckbox.setToolTip('Enable the use of Pixel Buffer Objects (PBOs)')
        pboCheckbox.setCursor(Qt.PointingHandCursor)
        pboCheckbox.setChecked(self.parent.parent.enablePBO)
        pboCheckbox.stateChanged.connect(self.togglePBO)
        pboCheckboxLabel = QLabel(' (recommended for 4K videos)')
        pboCheckboxLabel.setObjectName('checkboxsubtext')
        pboLabel = QLabel('''
            <b>ON:</b> usually improves performance with 4K videos but results in slower performance + latency with
            standard media due to higher memory use
            <br/>
            <b>OFF</b>: this should be your default choice for most media files
        ''', self)
        pboLabel.setObjectName('pbolabel')
        pboLabel.setTextFormat(Qt.RichText)
        pboLabel.setWordWrap(True)
        ratioCheckbox = QCheckBox('Keep aspect ratio', self)
        ratioCheckbox.setToolTip('Keep source video aspect ratio')
        ratioCheckbox.setCursor(Qt.PointingHandCursor)
        ratioCheckbox.setChecked(self.parent.parent.keepRatio)
        ratioCheckbox.stateChanged.connect(self.keepAspectRatio)
        ratioLabel = QLabel('''
            <b>OFF:</b> stretch video to application window size, ignored in fullscreen
            <br/>
            <b>ON:</b> lock video to its set video aspect, black bars added to compensate
        ''', self)
        ratioLabel.setObjectName('ratiolabel')
        ratioLabel.setTextFormat(Qt.RichText)
        ratioLabel.setWordWrap(True)
        videoLayout = QVBoxLayout()
        videoLayout.addWidget(decodingCheckbox)
        videoLayout.addWidget(decodingLabel)
        videoLayout.addLayout(SettingsDialog.lineSeparator())
        pboCheckboxLayout = QHBoxLayout()
        pboCheckboxLayout.setContentsMargins(0, 0, 0, 0)
        pboCheckboxLayout.addWidget(pboCheckbox)
        pboCheckboxLayout.addWidget(pboCheckboxLabel)
        pboCheckboxLayout.addStretch(1)
        videoLayout.addLayout(pboCheckboxLayout)
        videoLayout.addWidget(pboLabel)
        videoLayout.addLayout(SettingsDialog.lineSeparator())
        videoLayout.addWidget(ratioCheckbox)
        videoLayout.addWidget(ratioLabel)
        videoGroup = QGroupBox('Playback')
        videoGroup.setLayout(videoLayout)
        zoomLevel = self.parent.settings.value('videoZoom', 0, type=int)
        zoom_originalRadio = QRadioButton('No zoom [1:1]', self)
        zoom_originalRadio.setToolTip('1/1 No zoom')
        zoom_originalRadio.setCursor(Qt.PointingHandCursor)
        zoom_originalRadio.setChecked(zoomLevel == 0)
        zoom_qtrRadio = QRadioButton('Quarter [1:4]', self)
        zoom_qtrRadio.setToolTip('1/4 Zoom')
        zoom_qtrRadio.setCursor(Qt.PointingHandCursor)
        zoom_qtrRadio.setChecked(zoomLevel == -2)
        zoom_halfRadio = QRadioButton('Half [1:2]', self)
        zoom_halfRadio.setToolTip('1/2 Half')
        zoom_halfRadio.setCursor(Qt.PointingHandCursor)
        zoom_halfRadio.setChecked(zoomLevel == -1)
        zoom_doubleRadio = QRadioButton('Double [2:1]', self)
        zoom_doubleRadio.setToolTip('2/1 Double')
        zoom_doubleRadio.setCursor(Qt.PointingHandCursor)
        zoom_doubleRadio.setChecked(zoomLevel == 1)
        zoom_buttonGroup = QButtonGroup(self)
        zoom_buttonGroup.addButton(zoom_originalRadio, 3)
        zoom_buttonGroup.addButton(zoom_qtrRadio, 1)
        zoom_buttonGroup.addButton(zoom_halfRadio, 2)
        zoom_buttonGroup.addButton(zoom_doubleRadio, 4)
        # noinspection PyUnresolvedReferences
        zoom_buttonGroup.buttonClicked[int].connect(self.setZoom)
        zoomLayout = QGridLayout()
        zoomLayout.addWidget(zoom_originalRadio, 0, 0)
        zoomLayout.addWidget(zoom_qtrRadio, 0, 1)
        zoomLayout.addWidget(zoom_halfRadio, 1, 0)
        zoomLayout.addWidget(zoom_doubleRadio, 1, 1)
        zoomGroup = QGroupBox('Zoom')
        zoomGroup.setLayout(zoomLayout)
        noteLabel = QLabel('<b>NOTE:</b> video settings apply only to video playback and have no affect on the media '
                           'files you produce', self)
        noteLabel.setObjectName('zoomlabel')
        noteLabel.setTextFormat(Qt.RichText)
        noteLabel.setWordWrap(True)
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(15)
        mainLayout.addWidget(videoGroup)
        mainLayout.addWidget(zoomGroup)
        mainLayout.addWidget(noteLabel)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    @pyqtSlot(int)
    def switchDecoding(self, state: int) -> None:
        self.parent.parent.mpvWidget.property('hwdec', 'auto' if state == Qt.Checked else 'no')
        self.parent.parent.saveSetting('hwdec', state == Qt.Checked)
        self.parent.parent.hardwareDecoding = (state == Qt.Checked)

    @pyqtSlot(int)
    def togglePBO(self, state: int) -> None:
        self.parent.parent.mpvWidget.option('opengl-pbo', state == Qt.Checked)
        self.parent.parent.saveSetting('enablePBO', state == Qt.Checked)
        self.parent.parent.enablePBO = (state == Qt.Checked)

    @pyqtSlot(int)
    def keepAspectRatio(self, state: int) -> None:
        self.parent.parent.mpvWidget.option('keepaspect', state == Qt.Checked)
        self.parent.settings.setValue('aspectRatio', 'keep' if state == Qt.Checked else 'stretch')
        self.parent.parent.keepRatio = (state == Qt.Checked)

    @pyqtSlot(int)
    def setZoom(self, button_id: int) -> None:
        if button_id == 1:
            level = -2
        elif button_id == 2:
            level = -1
        elif button_id == 4:
            level = 1
        else:
            level = 0
        self.parent.parent.mpvWidget.property('video-zoom', level)
        self.parent.settings.setValue('videoZoom', level)


class ToolsPage(QWidget):
    def __init__(self, parent=None):
        super(ToolsPage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingstoolspage')
        self.ffmpegpath = QLineEdit(QDir.toNativeSeparators(self.parent.service.backends.ffmpeg), self)
        self.ffmpegpath.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        ffmpegbutton = QPushButton(self)
        ffmpegbutton.setIcon(QIcon(':/images/folder.png'))
        ffmpegbutton.setToolTip('Set FFmpeg path')
        ffmpegbutton.setCursor(Qt.PointingHandCursor)
        ffmpegbutton.clicked.connect(lambda c, backend='FFmpeg': self.setPath(backend, self.ffmpegpath))
        ffmpeglabel = QLabel('FFmpeg:', self)
        ffmpeglabel.setFixedWidth(65)
        ffmpeglayout = QHBoxLayout()
        ffmpeglayout.addWidget(ffmpeglabel)
        ffmpeglayout.addWidget(self.ffmpegpath)
        ffmpeglayout.addWidget(ffmpegbutton)
        self.ffprobepath = QLineEdit(QDir.toNativeSeparators(self.parent.service.backends.ffprobe), self)
        self.ffprobepath.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        ffprobebutton = QPushButton(self)
        ffprobebutton.setIcon(QIcon(':/images/folder.png'))
        ffprobebutton.setToolTip('Set FFprobe path')
        ffprobebutton.setCursor(Qt.PointingHandCursor)
        ffprobebutton.clicked.connect(lambda c, backend='FFprobe': self.setPath(backend, self.ffprobepath))
        ffprobelabel = QLabel('FFprobe:', self)
        ffprobelabel.setFixedWidth(65)
        ffprobelayout = QHBoxLayout()
        ffprobelayout.addWidget(ffprobelabel)
        ffprobelayout.addWidget(self.ffprobepath)
        ffprobelayout.addWidget(ffprobebutton)
        self.mediainfopath = QLineEdit(QDir.toNativeSeparators(self.parent.service.backends.mediainfo), self)
        self.mediainfopath.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        mediainfobutton = QPushButton(self)
        mediainfobutton.setIcon(QIcon(':/images/folder.png'))
        mediainfobutton.setToolTip('Set MediaInfo path')
        mediainfobutton.setCursor(Qt.PointingHandCursor)
        mediainfobutton.clicked.connect(lambda c, backend='MediaInfo': self.setPath(backend, self.mediainfopath))
        mediainfolabel = QLabel('MediaInfo:', self)
        mediainfolabel.setFixedWidth(65)
        mediainfolayout = QHBoxLayout()
        mediainfolayout.addWidget(mediainfolabel)
        mediainfolayout.addWidget(self.mediainfopath)
        mediainfolayout.addWidget(mediainfobutton)
        resetbutton = QPushButton('Reset to defaults', self)
        resetbutton.setObjectName('resetpathsbutton')
        resetbutton.setToolTip('Reset paths to their defaults')
        resetbutton.setCursor(Qt.PointingHandCursor)
        resetbutton.clicked.connect(self.resetPaths)
        resetlayout = QHBoxLayout()
        resetlayout.addStretch(1)
        resetlayout.addWidget(resetbutton)
        pathsLayout = QVBoxLayout()
        pathsLayout.setContentsMargins(11, 11, 11, 20)
        pathsLayout.addLayout(ffmpeglayout)
        pathsLayout.addLayout(ffprobelayout)
        pathsLayout.addLayout(mediainfolayout)
        pathsLayout.addLayout(resetlayout)
        pathsGroup = QGroupBox('Paths')
        pathsGroup.setLayout(pathsLayout)
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(15)
        mainLayout.addWidget(pathsGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    @pyqtSlot()
    def resetPaths(self) -> None:
        self.parent.settings.beginGroup('tools')
        self.parent.settings.setValue('ffmpeg', None)
        self.parent.settings.setValue('ffprobe', None)
        self.parent.settings.setValue('mediainfo', None)
        self.parent.settings.endGroup()
        self.parent.service.backends = VideoService.findBackends(self.parent.settings)
        self.ffmpegpath.setText(self.parent.service.backends.ffmpeg)
        self.ffprobepath.setText(self.parent.service.backends.ffprobe)
        self.mediainfopath.setText(self.parent.service.backends.mediainfo)

    def setPath(self, backend: str, field: QLineEdit) -> None:
        path = field.text()
        if path is None or not len(path):
            path = self.parent.parent.lastFolder if os.path.exists(self.parent.parent.lastFolder) else QDir.homePath()
        selectedpath, _ = QFileDialog.getOpenFileName(
            self,
            caption='Set {} path'.format(backend),
            directory=path,
            options=self.parent.parent.getFileDialogOptions())
        if selectedpath is not None and os.path.isfile(selectedpath) and os.access(selectedpath, os.X_OK):
            self.parent.service.backends[backend.lower()] = selectedpath
            self.parent.settings.setValue('tools/{}'.format(backend.lower()), selectedpath)
            field.setText(selectedpath)


class GeneralPage(QWidget):
    def __init__(self, parent=None):
        super(GeneralPage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingsgeneralpage')
        smartCutCheckbox = QCheckBox('Enable SmartCut mode')
        smartCutCheckbox.setToolTip('Enable SmartCut mode for frame-accurate cutting precision')
        smartCutCheckbox.setCursor(Qt.PointingHandCursor)
        smartCutCheckbox.setChecked(self.parent.parent.smartcut)
        smartCutCheckbox.stateChanged.connect(self.setSmartCut)
        smartCutCheckboxLabel = QLabel(' (frame-accurate cutting)')
        smartCutCheckboxLabel.setObjectName('checkboxsubtext')
        smartCutLabel1 = QLabel('<b>ON:</b> re-encode start + end portions of each clip at valid GOP (IDR) '
                                'keyframes')
        smartCutLabel1.setObjectName('smartcutlabel')
        smartCutLabel1.setWordWrap(True)
        smartCutLabel2 = QLabel('- slowest + most accurate mode')
        smartCutLabel2.setObjectName('smartcutlabel')
        smartCutLabel3 = QLabel('<b>OFF:</b> cut at nearest keyframe before/after your start/end markers')
        smartCutLabel3.setObjectName('smartcutlabel')
        smartCutLabel3.setWordWrap(True)
        smartCutLabel4 = QLabel('- fastest + less precise mode')
        smartCutLabel4.setObjectName('smartcutlabel')
        smartCutLayout = QGridLayout()
        smartCutLayout.setSpacing(0)
        smartCutLayout.setContentsMargins(25, 0, 5, 10)
        smartCutLayout.addWidget(smartCutLabel1, 0, 0, 1, 2)
        smartCutLayout.addItem(QSpacerItem(25, 1), 1, 0)
        smartCutLayout.addWidget(smartCutLabel2, 1, 1)
        smartCutLayout.addWidget(smartCutLabel3, 2, 0, 1, 2)
        smartCutLayout.addItem(QSpacerItem(25, 1), 3, 0)
        smartCutLayout.addWidget(smartCutLabel4, 3, 1)
        smartCutLayout.setColumnStretch(1, 1)
        smartCutCheckboxLayout = QHBoxLayout()
        smartCutCheckboxLayout.setContentsMargins(0, 0, 0, 0)
        smartCutCheckboxLayout.addWidget(smartCutCheckbox)
        smartCutCheckboxLayout.addWidget(smartCutCheckboxLabel)
        smartCutCheckboxLayout.addStretch(1)

        chaptersCheckbox = QCheckBox('Create chapters per clip', self)
        chaptersCheckbox.setToolTip('Automatically create chapters per clip')
        chaptersCheckbox.setCursor(Qt.PointingHandCursor)
        chaptersCheckbox.setChecked(self.parent.parent.createChapters)
        chaptersCheckbox.stateChanged.connect(self.createChapters)
        chaptersLabel = QLabel('''
            <b>ON:</b> existing chapters are ignored, new chapters added based on your clip index
            <br/>
            <b>OFF:</b> only chapters in source media are mapped to your file
        ''')
        chaptersLabel.setObjectName('chapterslabel')
        chaptersLabel.setTextFormat(Qt.RichText)
        chaptersLabel.setWordWrap(True)
        keepClipsCheckbox = QCheckBox('Keep clip segments', self)
        keepClipsCheckbox.setToolTip('Keep joined clip segments')
        keepClipsCheckbox.setCursor(Qt.PointingHandCursor)
        keepClipsCheckbox.setChecked(self.parent.parent.keepClips)
        keepClipsCheckbox.stateChanged.connect(self.keepClips)
        keepClipsLabel = QLabel('''
            <b>ON:</b> keep the clip segments set in your clip index after they have been joined 
            <br/>
            <b>OFF:</b> clip segments are automatically deleted once joined to produce your file
        ''', self)
        keepClipsLabel.setObjectName('keepclipslabel')
        keepClipsLabel.setTextFormat(Qt.RichText)
        keepClipsLabel.setWordWrap(True)
        self.singleInstance = self.parent.settings.value('singleInstance', 'on', type=str) in {'on', 'true'}
        singleInstanceCheckbox = QCheckBox('Allow only one running instance', self)
        singleInstanceCheckbox.setToolTip('Allow just one single {} instance to be running'
                                          .format(qApp.applicationName()))
        singleInstanceCheckbox.setCursor(Qt.PointingHandCursor)
        singleInstanceCheckbox.setChecked(self.singleInstance)
        singleInstanceCheckbox.stateChanged.connect(self.setSingleInstance)
        singleInstanceLabel = QLabel('''
            <b>ON:</b> allow only one single application window
            <br/>
            <b>OFF:</b> allow multiple application windows
        ''', self)
        singleInstanceLabel.setObjectName('singleinstancelabel')
        singleInstanceLabel.setTextFormat(Qt.RichText)
        singleInstanceLabel.setWordWrap(True)
        generalLayout = QVBoxLayout()
        generalLayout.addLayout(smartCutCheckboxLayout)
        generalLayout.addLayout(smartCutLayout)
        generalLayout.addLayout(SettingsDialog.lineSeparator())
        generalLayout.addWidget(chaptersCheckbox)
        generalLayout.addWidget(chaptersLabel)
        generalLayout.addLayout(SettingsDialog.lineSeparator())
        generalLayout.addWidget(keepClipsCheckbox)
        generalLayout.addWidget(keepClipsLabel)
        generalLayout.addLayout(SettingsDialog.lineSeparator())
        generalLayout.addWidget(singleInstanceCheckbox)
        generalLayout.addWidget(singleInstanceLabel)
        generalGroup = QGroupBox('General')
        generalGroup.setLayout(generalLayout)
        seek1SpinBox = QDoubleSpinBox(self)
        seek1SpinBox.setStyle(QStyleFactory.create('Fusion'))
        seek1SpinBox.setAttribute(Qt.WA_MacShowFocusRect, False)
        seek1SpinBox.setDecimals(1)
        seek1SpinBox.setRange(0.1, 999.9)
        seek1SpinBox.setSingleStep(0.1)
        seek1SpinBox.setSuffix(' secs')
        seek1SpinBox.setValue(self.parent.parent.level1Seek)
        # noinspection PyUnresolvedReferences
        seek1SpinBox.valueChanged[float].connect(lambda d: self.setSpinnerValue(1, d))
        seek2SpinBox = QDoubleSpinBox(self)
        seek2SpinBox.setStyle(QStyleFactory.create('Fusion'))
        seek2SpinBox.setAttribute(Qt.WA_MacShowFocusRect, False)
        seek2SpinBox.setDecimals(1)
        seek2SpinBox.setRange(0.1, 999.9)
        seek2SpinBox.setSingleStep(0.1)
        seek2SpinBox.setSuffix(' secs')
        seek2SpinBox.setValue(self.parent.parent.level2Seek)
        # noinspection PyUnresolvedReferences
        seek2SpinBox.valueChanged[float].connect(lambda d: self.setSpinnerValue(2, d))
        seekLabel = QLabel('''<b>NOTES:</b> these settings affect the seeking time forwards
            and backwards via the<br/>UP/DOWN and SHIFT + UP/DOWN keys. see the
            <i>Keyboard shortcuts</i> menu option for a full list of available shortcuts''', self)
        seekLabel.setObjectName('seeksettingslabel')
        seekLabel.setTextFormat(Qt.RichText)
        seekLabel.setWordWrap(True)
        spinnersLayout = QHBoxLayout()
        spinnersLayout.addStretch(1)
        spinnersLayout.addWidget(QLabel('Level #1: ', self))
        spinnersLayout.addWidget(seek1SpinBox)
        spinnersLayout.addStretch(1)
        spinnersLayout.addWidget(QLabel('Level #2: ', self))
        spinnersLayout.addWidget(seek2SpinBox)
        spinnersLayout.addStretch(1)
        seekLayout = QVBoxLayout()
        seekLayout.setContentsMargins(0, 0, 0, 0)
        seekLayout.setSpacing(0)
        seekLayout.addLayout(spinnersLayout)
        seekLayout.addWidget(seekLabel)
        self.seekGroup = QGroupBox('Seeking')
        self.seekGroup.setLayout(seekLayout)
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(15)
        mainLayout.addWidget(generalGroup)
        mainLayout.addWidget(self.seekGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    @pyqtSlot(int)
    def setSmartCut(self, state: int) -> None:
        self.parent.parent.toggleSmartCut(state == Qt.Checked)

    @pyqtSlot(int)
    def setSingleInstance(self, state: int) -> None:
        self.singleInstance = (state == Qt.Checked)
        self.parent.parent.saveSetting('singleInstance', self.singleInstance)

    @pyqtSlot(int)
    def createChapters(self, state: int) -> None:
        self.parent.parent.saveSetting('chapters', state == Qt.Checked)
        self.parent.parent.createChapters = (state == Qt.Checked)
        self.parent.parent.chaptersButton.setChecked(state == Qt.Checked)

    @pyqtSlot(int)
    def keepClips(self, state: int) -> None:
        self.parent.parent.saveSetting('keepClips', state == Qt.Checked)
        self.parent.parent.keepClips = (state == Qt.Checked)

    def setSpinnerValue(self, box_id: int, val: float) -> None:
        self.parent.settings.setValue('level{}Seek'.format(box_id), val)
        if box_id == 1:
            self.parent.parent.level1Seek = val
        elif box_id == 2:
            self.parent.parent.level2Seek = val

    def clearSpinners(self) -> None:
        for spinner in self.seekGroup.findChildren(QDoubleSpinBox):
            spinner.clearFocus()
            spinner.lineEdit().deselect()

    def showEvent(self, event: QShowEvent) -> None:
        self.clearSpinners()
        super(GeneralPage, self).showEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, service: VideoService, parent: QWidget, flags=Qt.WindowCloseButtonHint):
        super(SettingsDialog, self).__init__(parent.parentWidget(), flags)
        self.parent = parent
        self.service = service
        self.settings = self.parent.settings
        self.theme = self.parent.theme
        self.setObjectName('settingsdialog')
        if sys.platform in {'win32', 'darwin'}:
            self.setStyle(QStyleFactory.create('Fusion'))
        self.setWindowTitle('Settings')
        self.categories = QListWidget(self)
        self.categories.setResizeMode(QListView.Fixed)
        self.categories.setStyleSheet('QListView::item { text-decoration: none; }')
        self.categories.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.categories.setObjectName('settingsmenu')
        self.categories.setUniformItemSizes(True)
        self.categories.setMouseTracking(True)
        self.categories.setViewMode(QListView.IconMode)
        self.categories.setIconSize(QSize(90, 60))
        self.categories.setMovement(QListView.Static)
        self.categories.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pages = QStackedWidget(self)
        self.pages.addWidget(GeneralPage(self))
        self.pages.addWidget(VideoPage(self))
        self.pages.addWidget(ThemePage(self))
        self.pages.addWidget(ToolsPage(self))
        self.pages.addWidget(LogsPage(self))
        self.initCategories()
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(5)
        horizontalLayout.addWidget(self.categories)
        horizontalLayout.addWidget(self.pages, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, self)
        buttons.accepted.connect(self.close)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addWidget(buttons)
        self.setLayout(mainLayout)

    def initCategories(self):
        generalButton = QListWidgetItem(self.categories)
        generalButton.setIcon(QIcon(':/images/settings-general.png'))
        generalButton.setText('General')
        generalButton.setToolTip('General settings')
        generalButton.setTextAlignment(Qt.AlignHCenter)
        generalButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        videoButton = QListWidgetItem(self.categories)
        videoButton.setIcon(QIcon(':/images/settings-video.png'))
        videoButton.setText('Video')
        videoButton.setToolTip('Video settings')
        videoButton.setTextAlignment(Qt.AlignHCenter)
        videoButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        themeButton = QListWidgetItem(self.categories)
        themeButton.setIcon(QIcon(':/images/settings-theme.png'))
        themeButton.setText('Theme')
        themeButton.setToolTip('Theme settings')
        themeButton.setTextAlignment(Qt.AlignHCenter)
        themeButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        ffmpegButton = QListWidgetItem(self.categories)
        ffmpegButton.setIcon(QIcon(':/images/settings-ffmpeg.png'))
        ffmpegButton.setText('Tools')
        ffmpegButton.setToolTip('Tools settings')
        ffmpegButton.setTextAlignment(Qt.AlignHCenter)
        ffmpegButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        logsButton = QListWidgetItem(self.categories)
        logsButton.setIcon(QIcon(':/images/settings-logs.png'))
        logsButton.setText('Logs')
        logsButton.setToolTip('Logging settings')
        logsButton.setTextAlignment(Qt.AlignHCenter)
        logsButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.categories.currentItemChanged.connect(self.changePage)
        self.categories.setCurrentRow(0)
        self.categories.setMaximumWidth(self.categories.sizeHintForColumn(0) + 2)

    @staticmethod
    def lineSeparator() -> QHBoxLayout:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)
        layout.addSpacing(25)
        layout.addWidget(line)
        return layout

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def changePage(self, current: QListWidgetItem, previous: QListWidgetItem):
        if not current:
            current = previous
        index = self.categories.row(current)
        self.pages.setCurrentIndex(index)

    def sizeHint(self) -> QSize:
        return QSize(700 if sys.platform == 'darwin' else 625,
                     680 if sys.platform == 'darwin' else 645)
