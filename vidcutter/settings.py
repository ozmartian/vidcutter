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

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


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
            self.lightRadio.setToolTip('<img src=":/images/theme-light-large.jpg" />')
            self.lightRadio.setIconSize(QSize(165, 121))
            self.lightRadio.setCursor(Qt.PointingHandCursor)
            self.lightRadio.clicked.connect(self.switchTheme)
            self.lightRadio.setChecked(self.parent.theme == 'light')
            self.darkRadio = QRadioButton(self)
            self.darkRadio.setIcon(QIcon(':/images/%s/theme-dark.png' % self.parent.theme))
            self.darkRadio.setToolTip('<img src=":/images/theme-dark-large.jpg" />')
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
            themeGroup = QGroupBox('Theme selection')
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
        toolbar_buttonGroup.buttonClicked[int].connect(self.parent.parent.toolbar.setLabels)
        toolbarLayout = QGridLayout()
        toolbarLayout.addWidget(toolbar_iconsRadio, 0, 0)
        toolbarLayout.addWidget(toolbar_underRadio, 0, 1)
        toolbarLayout.addWidget(toolbar_besideRadio, 1, 0)
        toolbarGroup = QGroupBox('Toolbar labels')
        toolbarGroup.setLayout(toolbarLayout)
        mainLayout.addWidget(toolbarGroup)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    @pyqtSlot(bool)
    def switchTheme(self, checked: bool) -> None:
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
                <p>The application needs to be restarted in order to switch themes. Ensure you have saved
                your project or finished any cut ror join tasks in progress.</p>
                <p>Would you like to restart and switch themes now?</p>'''
                         % ('#C681D5' if self.parent.theme == 'dark' else '#642C68'))
            mbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            mbox.setDefaultButton(QMessageBox.Yes)
            response = mbox.exec_()
            if response == QMessageBox.Yes:
                self.parent.parent.theme = newtheme
                self.parent.parent.parent.reboot()


class VideoPage(QWidget):
    def __init__(self, parent=None):
        super(VideoPage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingsvideopage')


class GeneralPage(QWidget):
    def __init__(self, parent=None):
        super(GeneralPage, self).__init__(parent)
        self.parent = parent
        self.setObjectName('settingsgeneralpage')


class SettingsDialog(QDialog):
    def __init__(self, parent=None, flags=Qt.WindowCloseButtonHint):
        super(SettingsDialog, self).__init__(parent, flags)
        self.parent = parent
        self.settings = self.parent.settings
        self.theme = self.parent.theme
        self.setObjectName('settingsdialog')
        self.categories = QListWidget(self)
        self.categories.setStyleSheet('QListView::item { text-decoration: none; }')
        self.categories.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.categories.setObjectName('settingsmenu')
        self.categories.setUniformItemSizes(True)
        self.categories.setMouseTracking(True)
        self.categories.setViewMode(QListView.IconMode)
        self.categories.setIconSize(QSize(90, 50))
        self.categories.setMovement(QListView.Static)
        self.categories.setFixedWidth(105)
        self.categories.setCurrentRow(0)
        self.pages = QStackedWidget(self)
        self.pages.addWidget(ThemePage(self))
        self.pages.addWidget(VideoPage(self))
        self.pages.addWidget(GeneralPage(self))
        self.initCategories()
        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.categories)
        horizontalLayout.addWidget(self.pages, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, self)
        buttons.accepted.connect(self.close)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addSpacing(12)
        mainLayout.addWidget(buttons)
        self.setLayout(mainLayout)
        self.setWindowTitle('Settings - {0}'.format(qApp.applicationName()))
        self.setFixedSize(565, 385)

    def initCategories(self):
        themeButton = QListWidgetItem(self.categories)
        themeButton.setIcon(QIcon(':/images/{0}/settings-theme.png'.format(self.parent.theme)))
        themeButton.setText('Theme')
        themeButton.setToolTip('Theme settings')
        themeButton.setTextAlignment(Qt.AlignHCenter)
        themeButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        videoButton = QListWidgetItem(self.categories)
        videoButton.setIcon(QIcon(':/images/{0}/settings-video.png'.format(self.parent.theme)))
        videoButton.setText('Video')
        videoButton.setToolTip('Video settings')
        videoButton.setTextAlignment(Qt.AlignHCenter)
        videoButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        generalButton = QListWidgetItem(self.categories)
        generalButton.setIcon(QIcon(':/images/{0}/settings-general.png'.format(self.parent.theme)))
        generalButton.setText('General')
        generalButton.setToolTip('General settings')
        generalButton.setTextAlignment(Qt.AlignHCenter)
        generalButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.categories.currentItemChanged.connect(self.changePage)
        self.categories.adjustSize()

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def changePage(self, current: QListWidgetItem, previous: QListWidgetItem):
        if not current:
            current = previous
        index = self.categories.row(current)
        self.pages.setCurrentIndex(index)

    @pyqtSlot()
    def closeEvent(self, event: QCloseEvent):
        self.deleteLater()
        super(SettingsDialog, self).closeEvent(event)
