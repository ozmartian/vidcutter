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

import sys

from PyQt5.QtCore import pyqtSlot, QSize, Qt
from PyQt5.QtGui import QCloseEvent, QIcon, QShowEvent
from PyQt5.QtWidgets import (qApp, QButtonGroup, QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFrame,
                             QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListView, QListWidget, QListWidgetItem,
                             QMessageBox, QRadioButton, QStackedWidget, QStyleFactory, QVBoxLayout, QWidget)


class LogsPage(QWidget):
    def __init__(self, parent=None):
        super(LogsPage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingslogspage')
        verboseCheckbox = QCheckBox('Enable verbose logging', self)
        verboseCheckbox.setToolTip('Detailed log ouput to log file and console')
        verboseCheckbox.setCursor(Qt.PointingHandCursor)
        verboseCheckbox.setChecked(self.parent.parent.verboseLogs)
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
        mainLayout.setSpacing(10)
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
        mainLayout.setSpacing(10)
        if sys.platform != 'darwin':
            self.lightRadio = QRadioButton(self)
            self.lightRadio.setIcon(QIcon(':/images/%s/theme-light.png' % self.parent.theme))
            self.lightRadio.setIconSize(QSize(165, 121))
            self.lightRadio.setCursor(Qt.PointingHandCursor)
            self.lightRadio.clicked.connect(self.switchTheme)
            self.lightRadio.setChecked(self.parent.theme == 'light')
            self.darkRadio = QRadioButton(self)
            self.darkRadio.setIcon(QIcon(':/images/%s/theme-dark.png' % self.parent.theme))
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
        toolbar_labels = self.parent.settings.value('toolbarLabels', 'beside', type=str)
        toolbar_iconsRadio = QRadioButton('Icons only', self)
        toolbar_iconsRadio.setToolTip('Icons only')
        toolbar_iconsRadio.setCursor(Qt.PointingHandCursor)
        toolbar_iconsRadio.setChecked(toolbar_labels == 'none')
        toolbar_underRadio = QRadioButton('Text under icons', self)
        toolbar_underRadio.setToolTip('Text under icons')
        toolbar_underRadio.setCursor(Qt.PointingHandCursor)
        toolbar_underRadio.setChecked(toolbar_labels == 'under')
        toolbar_besideRadio = QRadioButton('Text beside icons', self)
        toolbar_besideRadio.setToolTip('Text beside icons')
        toolbar_besideRadio.setCursor(Qt.PointingHandCursor)
        toolbar_besideRadio.setChecked(toolbar_labels == 'beside')
        toolbar_buttonGroup = QButtonGroup(self)
        toolbar_buttonGroup.addButton(toolbar_iconsRadio, 1)
        toolbar_buttonGroup.addButton(toolbar_underRadio, 2)
        toolbar_buttonGroup.addButton(toolbar_besideRadio, 3)
        # noinspection PyUnresolvedReferences
        toolbar_buttonGroup.buttonClicked[int].connect(self.parent.parent.toolbar.setLabels)
        toolbarLayout = QGridLayout()
        toolbarLayout.addWidget(toolbar_besideRadio, 0, 0)
        toolbarLayout.addWidget(toolbar_underRadio, 0, 1)
        toolbarLayout.addWidget(toolbar_iconsRadio, 1, 0)
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
                        font-family: "Futura-Light", sans-serif;
                        font-weight: 400;
                    }
                    p { font-size: 15px; }
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
            <b>ON:</b> saves laptop power + prevents video tearing;
            falls back to software decoding if hardware not supported
            <br/>
            <b>OFF:</b> always use software based decoding''', self)
        decodingLabel.setObjectName('decodinglabel')
        decodingLabel.setTextFormat(Qt.RichText)
        decodingLabel.setWordWrap(True)
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
        videoLayout.addWidget(SettingsDialog.lineSeparator())
        videoLayout.addWidget(ratioCheckbox)
        videoLayout.addWidget(ratioLabel)
        videoGroup = QGroupBox('Playback')
        videoGroup.setLayout(videoLayout)
        zoomLevel = self.parent.settings.value('videoZoom', 0, type=int)
        zoom_qtrRadio = QRadioButton('Quarter [1:4]', self)
        zoom_qtrRadio.setToolTip('1/4 Zoom')
        zoom_qtrRadio.setCursor(Qt.PointingHandCursor)
        zoom_qtrRadio.setChecked(zoomLevel == -2)
        zoom_halfRadio = QRadioButton('Half [1:2]', self)
        zoom_halfRadio.setToolTip('1/2 Half')
        zoom_halfRadio.setCursor(Qt.PointingHandCursor)
        zoom_halfRadio.setChecked(zoomLevel == -1)
        zoom_originalRadio = QRadioButton('No zoom [1:1]', self)
        zoom_originalRadio.setToolTip('1/1 No zoom')
        zoom_originalRadio.setCursor(Qt.PointingHandCursor)
        zoom_originalRadio.setChecked(zoomLevel == 0)
        zoom_doubleRadio = QRadioButton('Double [2:1]', self)
        zoom_doubleRadio.setToolTip('2/1 Double')
        zoom_doubleRadio.setCursor(Qt.PointingHandCursor)
        zoom_doubleRadio.setChecked(zoomLevel == 1)
        zoom_buttonGroup = QButtonGroup(self)
        zoom_buttonGroup.addButton(zoom_qtrRadio, 1)
        zoom_buttonGroup.addButton(zoom_halfRadio, 2)
        zoom_buttonGroup.addButton(zoom_originalRadio, 3)
        zoom_buttonGroup.addButton(zoom_doubleRadio, 4)
        # noinspection PyUnresolvedReferences
        zoom_buttonGroup.buttonClicked[int].connect(self.setZoom)
        zoomLayout = QGridLayout()
        zoomLayout.addWidget(zoom_qtrRadio, 0, 0)
        zoomLayout.addWidget(zoom_halfRadio, 0, 1)
        zoomLayout.addWidget(zoom_originalRadio, 1, 0)
        zoomLayout.addWidget(zoom_doubleRadio, 1, 1)
        zoomGroup = QGroupBox('Zoom')
        zoomGroup.setLayout(zoomLayout)
        noteLabel = QLabel('<b>NOTE:</b> video settings apply only to video playback and have no affect on the media '
                           'files you produce', self)
        noteLabel.setObjectName('zoomlabel')
        noteLabel.setTextFormat(Qt.RichText)
        noteLabel.setWordWrap(True)
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(10)
        mainLayout.addWidget(videoGroup)
        mainLayout.addWidget(zoomGroup)
        mainLayout.addWidget(noteLabel)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    @pyqtSlot(int)
    def switchDecoding(self, state: int) -> None:
        self.parent.parent.mpvWidget.mpv.set_property('hwdec', 'auto' if state == Qt.Checked else 'no')
        self.parent.parent.saveSetting('hwdec', state == Qt.Checked)
        self.parent.parent.hardwareDecoding = (state == Qt.Checked)

    @pyqtSlot(int)
    def keepAspectRatio(self, state: int) -> None:
        self.parent.parent.mpvWidget.mpv.set_option('keepaspect', state == Qt.Checked)
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
        self.parent.parent.mpvWidget.mpv.set_property('video-zoom', level)
        self.parent.settings.setValue('videoZoom', level)


class GeneralPage(QWidget):
    def __init__(self, parent=None):
        super(GeneralPage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingsgeneralpage')
        smartCutCheckbox = QCheckBox('Enable SmartCut (frame-accurate mode)')
        smartCutCheckbox.setToolTip('Enable SmartCut mode for frame-accurate precision when cutting')
        smartCutCheckbox.setCursor(Qt.PointingHandCursor)
        smartCutCheckbox.setChecked(self.parent.parent.smartcut)
        smartCutCheckbox.stateChanged.connect(self.setSmartCut)
        self.smartCutLabel = QLabel('''
            <b>ON:</b> re-encode start + end portions of each clip at valid GOP (IDR) keyframes
            <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            - slowest + most accurate mode
            <br/>
            <b>OFF:</b> cut at nearest keyframe before/after your start/end markers
            <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            - fastest + less precise mode''', self)
        self.smartCutLabel.setObjectName('smartcutlabel')
        self.smartCutLabel.setTextFormat(Qt.RichText)
        self.smartCutLabel.setAlignment(Qt.AlignTop)
        self.smartCutLabel.setWordWrap(True)
        if sys.platform != 'win32':
            self.smartCutLabel.setMinimumHeight(self.smartCutLabel.heightForWidth(self.sizeHint().width()))
        self.singleInstance = self.parent.settings.value('singleInstance', 'on', type=str) in {'on', 'true'}
        singleInstanceCheckbox = QCheckBox('Allow only one running instance', self)
        singleInstanceCheckbox.setToolTip('Allow just one single %s instance to be running' % qApp.applicationName())
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
        generalLayout = QVBoxLayout()
        generalLayout.addWidget(smartCutCheckbox)
        generalLayout.addWidget(self.smartCutLabel)
        generalLayout.addWidget(SettingsDialog.lineSeparator())
        generalLayout.addWidget(keepClipsCheckbox)
        generalLayout.addWidget(keepClipsLabel)
        generalLayout.addWidget(SettingsDialog.lineSeparator())
        generalLayout.addWidget(singleInstanceCheckbox)
        generalLayout.addWidget(singleInstanceLabel)
        generalGroup = QGroupBox('General')
        generalGroup.setLayout(generalLayout)
        seek1SpinBox = QDoubleSpinBox(self)
        seek1SpinBox.setDecimals(1)
        seek1SpinBox.setRange(0.1, 999.9)
        seek1SpinBox.setSingleStep(0.1)
        seek1SpinBox.setSuffix(' secs')
        seek1SpinBox.setValue(self.parent.parent.level1Seek)
        # noinspection PyUnresolvedReferences
        seek1SpinBox.valueChanged[float].connect(lambda d: self.setSpinnerValue(1, d))
        seek1Layout = QHBoxLayout()
        seek1Layout.addStretch(1)
        seek1Layout.addWidget(QLabel('Level #1'))
        seek1Layout.addWidget(seek1SpinBox)
        seek1Layout.addStretch(1)
        seek2SpinBox = QDoubleSpinBox(self)
        seek2SpinBox.setDecimals(1)
        seek2SpinBox.setRange(0.1, 999.9)
        seek2SpinBox.setSingleStep(0.1)
        seek2SpinBox.setSuffix(' secs')
        seek2SpinBox.setValue(self.parent.parent.level2Seek)
        # noinspection PyUnresolvedReferences
        seek2SpinBox.valueChanged[float].connect(lambda d: self.setSpinnerValue(2, d))
        seekLabel = QLabel('''
            <b>NOTE:</b> these settings affect the seeking time forwards and backwards
            via the UP/DOWN and SHIFT + UP/DOWN keys. see the <i>Keyboard shortcuts</i> menu
            option for a full list of available shortcuts
        ''', self)
        seekLabel.setObjectName('seeksettingslabel')
        seekLabel.setTextFormat(Qt.RichText)
        seekLabel.setWordWrap(True)
        seek2Layout = QHBoxLayout()
        seek2Layout.addStretch(1)
        seek2Layout.addWidget(QLabel('Level #2'))
        seek2Layout.addWidget(seek2SpinBox)
        seek2Layout.addStretch(1)
        seekWidgetsLayout = QHBoxLayout()
        seekWidgetsLayout.addLayout(seek1Layout)
        seekWidgetsLayout.addLayout(seek2Layout)
        seekLayout = QVBoxLayout()
        seekLayout.addLayout(seekWidgetsLayout)
        seekLayout.addWidget(seekLabel)
        self.seekGroup = QGroupBox('Seeking')
        self.seekGroup.setLayout(seekLayout)
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(10)
        mainLayout.addWidget(generalGroup)
        mainLayout.addWidget(self.seekGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)
        if sys.platform == 'win32':
            seek1SpinBox.setStyle(QStyleFactory.create('Fusion'))
            seek2SpinBox.setStyle(QStyleFactory.create('Fusion'))

    @pyqtSlot(int)
    def setSmartCut(self, state: int) -> None:
        self.parent.parent.toggleSmartCut(state == Qt.Checked)

    @pyqtSlot(int)
    def setSingleInstance(self, state: int) -> None:
        self.singleInstance = (state == Qt.Checked)
        self.parent.parent.saveSetting('singleInstance', self.singleInstance)

    @pyqtSlot(int)
    def keepClips(self, state: int) -> None:
        self.parent.parent.saveSetting('keepClips', state == Qt.Checked)
        self.parent.parent.keepClips = (state == Qt.Checked)

    def setSpinnerValue(self, box_id: int, val: float) -> None:
        self.parent.settings.setValue('level{0}Seek'.format(box_id), val)
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
    def __init__(self, parent=None, flags=Qt.WindowCloseButtonHint):
        super(SettingsDialog, self).__init__(parent.parent, flags)
        self.parent = parent
        self.settings = self.parent.settings
        self.theme = self.parent.theme
        self.setObjectName('settingsdialog')
        self.setWindowTitle('Settings - {0}'.format(qApp.applicationName()))
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
        self.pages.addWidget(LogsPage(self))
        self.initCategories()
        horizontalLayout = QHBoxLayout()
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
        logsButton = QListWidgetItem(self.categories)
        logsButton.setIcon(QIcon(':/images/settings-logs.png'))
        logsButton.setText('Logs')
        logsButton.setToolTip('Logging settings')
        logsButton.setTextAlignment(Qt.AlignHCenter)
        logsButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.categories.currentItemChanged.connect(self.changePage)
        self.categories.setCurrentRow(0)
        self.categories.setMaximumWidth(self.categories.sizeHintForColumn(0) + 2)
        self.setMinimumWidth(650 if sys.platform == 'darwin' else 620)
        if sys.platform != 'win32':
            self.adjustSize()

    @staticmethod
    def lineSeparator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def changePage(self, current: QListWidgetItem, previous: QListWidgetItem):
        if not current:
            current = previous
        index = self.categories.row(current)
        self.pages.setCurrentIndex(index)

    @pyqtSlot(QCloseEvent)
    def closeEvent(self, event: QCloseEvent):
        self.deleteLater()
        super(SettingsDialog, self).closeEvent(event)
