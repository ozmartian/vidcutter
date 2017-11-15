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

import os
import platform
import sys
from datetime import datetime

from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import QPoint, QSize, Qt, QUrl
from PyQt5.QtGui import QCloseEvent, QPixmap
from PyQt5.QtWidgets import qApp, QDialog, QDialogButtonBox, QLabel, QTabWidget, QTextBrowser, QVBoxLayout
from sip import SIP_VERSION_STR

import vidcutter
import vidcutter.libs.mpv as mpv


class About(QDialog):
    def __init__(self, parent=None, f=Qt.WindowCloseButtonHint):
        super(About, self).__init__(parent, f)
        self.parent = parent
        self.setObjectName('aboutwidget')
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowModality(Qt.ApplicationModal)
        builddate = datetime.fromtimestamp(os.path.getmtime(mpv.__file__)).strftime('%d %b %Y')
        pencolor1 = '#9A45A2' if self.parent.theme == 'dark' else '#642C68'
        pencolor2 = '#FFF' if self.parent.theme == 'dark' else '#000'
        appicon = self.parent.getAppIcon(encoded=True)
        header = QLabel('''
        <style>table { color: %s; background-color: transparent; }</style>
        <table border="0" cellpadding="5" cellspacing="1" width="100%%">
            <tr>
                <td width="82" style="padding-top:10px;padding-right:10px;">
                    <img src="%s" width="82" />
                </td>
                <td style="padding:4px;">
                    <div style="font-family:'Futura-Light', sans-serif;font-size:40px;font-weight:400;color:%s;">
                        <span style="font-size:58px;">V</span>ID<span style="font-size:58px;">C</span>UTTER
                    </div>
                    &nbsp;&nbsp;
                    <div style="padding:0; margin:0; margin-left:10px;">
                        <table border="0" cellpadding="2" cellspacing="0">
                        <tr valign="middle">
                            <td style="text-align:right;font-size:10pt;font-weight:500;color:%s;">version:</td>
                            <td>
                                <span style="font-size:18px;font-weight:400;">%s</span>
                                &nbsp;<span style="font-size:10pt;margin-left:5px;">(%s)</span>
                            </td>
                        </tr>
                        <tr valign="middle">
                            <td style="text-align:right;font-size:10pt;font-weight:500;color:%s;">build date:</td>
                            <td style="font-size:10pt;font-weight:400;">%s</td>
                        </tr>
                        </table>
                    </div>
                </td>
                <td valign="bottom" align="right" style="padding:30px 15px 15px 15px;">
                    <div style="padding:20px 0 10px 0;">
                        <img src=":/images/%s/python.png"/>
                    </div>
                    <div style="margin-top:10px;">
                        <img src=":/images/qt.png" />
                    </div>
                </td>
            </tr>
        </table>''' % (pencolor2, appicon, pencolor1, pencolor1, qApp.applicationVersion(), platform.architecture()[0],
                       pencolor1, builddate.upper(), self.parent.theme), self)
        header.setStyleSheet('border:none;')
        self.tab_about = AboutTab(self)
        self.tab_credits = CreditsTab(self)
        self.tab_license = LicenseTab(self)
        tabs = QTabWidget()
        tabs.addTab(self.tab_about, 'About')
        tabs.addTab(self.tab_credits, 'Credits')
        tabs.addTab(self.tab_license, 'License')
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.close)
        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(tabs)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setWindowTitle('About %s' % qApp.applicationName())
        self.setWindowIcon(self.parent.windowIcon())
        self.setMinimumSize(self.get_size(self.parent.parent.scale))

    @staticmethod
    def get_size(mode: str = 'NORMAL') -> QSize:
        modes = {
            'LOW': QSize(450, 300),
            'NORMAL': QSize(515, 520),
            'HIGH': QSize(1080, 920)
        }
        return modes[mode]

    def closeEvent(self, event: QCloseEvent) -> None:
        self.tab_about.deleteLater()
        self.tab_credits.deleteLater()
        self.tab_license.deleteLater()
        self.deleteLater()
        event.accept()


class BaseTab(QTextBrowser):
    def __init__(self, parent=None):
        super(BaseTab, self).__init__(parent)
        self.setOpenExternalLinks(True)
        if parent.parent.theme == 'dark':
            self.setStyleSheet('QTextBrowser { background-color: rgba(12, 15, 16, 210); color: #FFF; }')
        else:
            self.setStyleSheet('QTextBrowser { background-color: rgba(255, 255, 255, 200); color: #000; }')


class AboutTab(BaseTab):
    def __init__(self, parent=None):
        super(AboutTab, self).__init__(parent)
        self.parent = parent
        linebreak = '<br/>' if sys.platform == 'win32' else '&nbsp;&nbsp;&nbsp;'
        # noinspection PyBroadException
        try:
            ffmpeg_version = self.parent.parent.videoService.version()
        except BaseException:
            ffmpeg_version = '<span style="color:red;">MISSING</span>'
        html = '''
<style>
    table { width: 100%%; font-family: "Noto Sans UI", sans-serif; }
    a { color: %s; text-decoration: none; font-weight: bold; }
</style>
<table border="0" cellpadding="8" cellspacing="4">
    <tr>
        <td>
            <table border="0" cellpadding="0" cellspacing="0">
                <tr valign="bottom">
                    <td>
                        <p style="font-size:13px;">
                            <b>libmpv:</b> %s
                            %s
                            <b>FFmpeg:</b> %s
                            <br/>
                            <b>Python:</b> %s
                            &nbsp;&nbsp;&nbsp;
                            <b>PyQt5:</b> %s
                            &nbsp;&nbsp;&nbsp;
                            <b>SIP:</b> %s
                        </p>
                        <p style="font-size:13px;">
                            Copyright &copy; %s <a href="mailto:%s">%s</a>
                            <br/>
                            Website: <a href="%s" target="_blank">%s</a>
                        </p>
                        <p style="font-size:13px;">
                            Found a bug? You can <a href="%s">REPORT IT HERE</a>.
                        </p>
                    </td>
                    <td align="right">
                        <a href="https://www.jetbrains.com/pycharm"><img src=":/images/pycharm.png" /></a>
                    </td>
                </tr>
            </table>
            <p style="font-size:12px;">
                Built in Python with the help of <a href="https://www.jetbrains.com/pycharm">PyCharm Professional</a>
                using an open-source development license donated by its wickedly cool creators at
                <a href="https://www.jetbrains.com">JetBrains</a>.
            </p>
            <p style="font-size:11px; margin-top:15px;">
                This program is free software; you can redistribute it and/or
                modify it under the terms of the GNU General Public License
                version 3, or (at your option) any later version. This software uses code
                produced by the <a href="https://mpv.io">mpv</a> and
                <a href="https://www.ffmpeg.org">FFmpeg</a> projects under the
                <a href="https://www.gnu.org/licenses/old-licenses/gpl-2.0.html">GPLv2.0</a> and
                <a href="https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html">LGPLv2.1</a>
                licenses respectively.
            </p>
        </td>
    </tr>
</table>''' % ('#EA95FF' if self.parent.parent.theme == 'dark' else '#441D4E',
               self.parent.parent.mpvWidget.mpv.get_property('mpv-version').replace('mpv ', ''), linebreak,
               ffmpeg_version, sys.version.split(' ')[0], PYQT_VERSION_STR, SIP_VERSION_STR, datetime.now().year,
               vidcutter.__email__, vidcutter.__author__, vidcutter.__website__, vidcutter.__website__,
               vidcutter.__bugreport__)
        self.setHtml(html)


class CreditsTab(BaseTab):
    def __init__(self, parent=None):
        super(CreditsTab, self).__init__(parent)
        self.parent = parent
        self.setObjectName('credits')
        self.setHtml('''<style>a { color:%s; text-decoration:none; font-weight:bold; }
        a:hover { text-decoration:underline; }</style>
        <h3 style="text-align:center;">CREDITS</h3>
        <p>
            This application either uses code and tools from the following projects in part or in their entirety as
            deemed permissable by each project's open-source license.
        </p>
        <table border="0" cellpadding="10" cellspacing="0" width="400" align="center" style="margin-top:10px;">
            <tr>
                <td width="200">
                    <p>
                        <a href="https://github.com/marcan/pympv">pympv</a>
                        -
                        GPLv3+
                    </p>
                    <p>
                        <a href="http://ffmpeg.org">FFmpeg</a>
                        -
                        GPLv2+
                    </p>
                    <p>
                        <a href="https://www.riverbankcomputing.com/software/pyqt">PyQt5</a>
                        -
                        GPLv3+
                    </p>
                </td>
                <td width="200">
                    <p>
                        <a href="http://mpv.io">mpv (libmpv)</a>
                        -
                        GPLv2+
                    </p>
                    <p>
                        <a href="http://mediaarea.net/mediainfo">MediaInfo</a>
                        -
                        BSD-style
                    </p>
                    <p>
                        <a href="https://www.qt.io">Qt5</a>
                        -
                        LGPLv3
                    </p>
                </td>
            </tr>
        </table>''' % ('#EA95FF' if self.parent.parent.theme == 'dark' else '#441D4E'))


class LicenseTab(BaseTab):
    def __init__(self, parent=None):
        super(LicenseTab, self).__init__(parent)
        self.setObjectName('license')
        self.setSource(QUrl('qrc:/license.html'))
