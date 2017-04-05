#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - a simple yet fast & accurate video cutter & joiner
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

import platform
import sys

from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import QSize, Qt, QUrl
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QTabWidget, QTextBrowser, QVBoxLayout, qApp)
from sip import SIP_VERSION_STR


class AppInfo(QDialog):
    def __init__(self, parent=None, f=Qt.WindowCloseButtonHint):
        super(AppInfo, self).__init__(parent, f)
        self.parent = parent
        self.setObjectName('aboutwidget')
        self.setWindowModality(Qt.ApplicationModal)
        header = QLabel('''
            <style>table { color: #000; background-color: transparent; }</style>
            <table border="0" cellpadding="5" cellspacing="1" width="100%%">
                <tr>
                    <td width="82">
                        <img src=":/images/vidcutter-small.png" width="82" />
                    </td>
                    <td style="padding:4px;">
                        <span style="font-family:'Futura LT', sans-serif;font-size:40px;font-weight:500;color:#642C68;">
                            <span style="font-size:58px;">V</span>ID<span style="font-size:58px;">C</span>UTTER
                        </span>
                        <br/>&nbsp;&nbsp;
                        <span style="font-size:16px;">version %s</span>
                        <span style="font-size:10pt;margin-left:5px;">- %s</span>
                    </td>
                    <td align="right" style="padding:15px;">
                        <div style="padding:20px 0 10px 0;">
                            <img src=":/images/python.png"/>
                        </div>
                        <div style="margin-top:10px;">
                            <img src=":/images/qt.png" />
                        </div>
                    </td>
                </tr>
            </table>''' % (qApp.applicationVersion(), platform.architecture()[0]), self)
        header.setStyleSheet('border:none;')
        self.tab_about = AboutTab(self)
        self.tab_credits = CreditsTab()
        self.tab_license = LicenseTab()
        tabs = QTabWidget()
        tabs.setFocusPolicy(Qt.NoFocus)
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

    def get_size(self, mode: str = 'NORMAL') -> QSize:
        modes = {
            'LOW': QSize(450, 250),
            'NORMAL': QSize(540, 430),
            'HIGH': QSize(1080, 840)
        }
        return modes[mode]

    def closeEvent(self, event: QCloseEvent):
        self.tab_about.deleteLater()
        self.tab_credits.deleteLater()
        self.tab_license.deleteLater()
        self.deleteLater()
        event.accept()


class BaseTab(QTextBrowser):
    def __init__(self, parent=None):
        super(BaseTab, self).__init__(parent)
        self.setOpenExternalLinks(True)


class AboutTab(BaseTab):
    def __init__(self, parent=None):
        super(AboutTab, self).__init__(parent)
        self.parent = parent
        weight = 500 if sys.platform == 'win32' else 600
        linebreak = '<br/>' if sys.platform == 'win32' else '&nbsp;&nbsp;&nbsp;'
        try:
            ffmpeg_version = self.parent.parent.mediaPlayer.ffmpeg_version
        except AttributeError:
            ffmpeg_version = '2.8.10'
        html = '''
<style>
    a { color:#441d4e; text-decoration:none; font-weight:bold; }
    a:hover { text-decoration:underline; }
    table { width: 100%%; font-family: "Open Sans", sans-serif; }
</style>
<table border="0" cellpadding="8" cellspacing="4">
    <tr>
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
                Copyright &copy; 2017 <a href="mailto:pete@ozmartians.com">Pete Alexandrou</a>
                <br/>
                Website: <a href="http://vidcutter.ozmartians.com">http://vidcutter.ozmartians.com</a>
            </p>
            <p style="font-size:13px;">
                Icon design by <a href="https://github.com/PapirusDevelopmentTeam">Papirus
                Development Team</a>
            </p>
            <p style="font-size:11px; margin-top:15px;">
                This program is free software; you can redistribute it and/or
                modify it under the terms of the GNU General Public License
                version 3, or (at your option) any later version.
                This software uses libraries from the <a href="https://mpv.io">mpv</a> and
                <a href="https://www.ffmpeg.org">FFmpeg</a> projects under the
                <a href="https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html">LGPLv2.1</a> license.
            </p>
        </td>
    </tr>
</table>''' % (self.parent.parent.mediaPlayer.mpv_version.replace('mpv ', ''), linebreak,
               ffmpeg_version, sys.version.split(' ')[0], PYQT_VERSION_STR, SIP_VERSION_STR)
        self.setHtml(html)


class CreditsTab(BaseTab):
    def __init__(self):
        super(CreditsTab, self).__init__()
        self.setObjectName('credits')
        self.setHtml('''<style>a { color:#441d4e; text-decoration:none; font-weight:bold; }
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
                        <a href="http://ffmpeg.org">FFmpeg</a>
                        -
                        GPLv2+
                    </p>
                    <p>
                        <a href="http://mpv.io">mpv</a>
                        -
                        GPLv2+
                    </p>
                    <p>
                        <a href="https://mpv.srsfckn.biz">libmpv</a>
                        -
                        GPLv3+
                    </p>
                    <p>
                        <a href="https://github.com/jaseg/python-mpv">python-mpv</a>
                        -
                        AGPLv3
                    </p>
                </td>
                <td width="200">
                    <p>
                        <a href="http://mediaarea.net/mediainfo">MediaInfo</a>
                        -
                        BSD-style
                    </p>
                    <p>
                        <a href="https://www.riverbankcomputing.com/software/pyqt">PyQt5</a>
                        -
                        GPLv3+
                    </p>
                    <p>
                        <a href="https://www.qt.io">Qt5</a>
                        -
                        LGPLv3
                    </p>
                </td>
            </tr>
        </table>''')


class LicenseTab(BaseTab):
    def __init__(self):
        super(LicenseTab, self).__init__()
        self.setObjectName('license')
        self.setSource(QUrl('qrc:/LICENSE.html'))
