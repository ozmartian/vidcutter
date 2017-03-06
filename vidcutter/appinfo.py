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
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTabWidget, QTextBrowser, QVBoxLayout, qApp
from sip import SIP_VERSION_STR


class AppInfo(QDialog):
    def __init__(self, parent=None, f=Qt.WindowCloseButtonHint):
        super(AppInfo, self).__init__(parent, f)
        self.parent = parent
        self.setObjectName('aboutwidget')
        self.setWindowModality(Qt.ApplicationModal)
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
        layout.addWidget(tabs)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setWindowTitle('About %s' % qApp.applicationName())
        self.setWindowIcon(self.parent.windowIcon())
        self.setMinimumSize(585, 430)

    def closeEvent(self, event: QCloseEvent):
        self.tab_about.deleteLater()
        self.tab_credits.deleteLater()
        self.tab_license.deleteLater()
        self.deleteLater()
        event.accept()


class AboutTab(QTextBrowser):
    def __init__(self, parent=None):
        super(AboutTab, self).__init__(parent)
        self.parent = parent
        weight = 500 if sys.platform == 'win32' else 600
        linebreak = '<br/>' if sys.platform == 'win32' else '&nbsp;&nbsp;&nbsp;'
        try:
            ffmpeg_version = self.parent.parent.mediaPlayer.ffmpeg_version
        except AttributeError:
            ffmpeg_version = '2.8.10'
        self.setHtml('''<style>
    a { color:#441d4e; text-decoration:none; font-weight:bold; }
    a:hover { text-decoration:underline; }
    table { width: 100%%; font-family: "Open Sans", sans-serif; }
</style>
<table border="0" cellpadding="6" cellspacing="4">
    <tr>
        <td>
            <img src=":/images/vidcutter.png" />
        </td>
        <td>
            <p>
                <span style="font-size:36pt; font-weight:%i; color:#6A4572;">%s</span>
                <br/>
                &nbsp;&nbsp;
                <span style="font-size:13pt;font-weight:600;">Version:</span>
                <span style="font-size:13pt;font-weight:%i;">%s</span>
                <span style="font-size:10pt;position:relative;left:5px;">- %s</span>
            </p>
            <p style="font-size:13px;">
                + <b>libmpv:</b> %s
                %s
                + <b>FFmpeg:</b> %s
                <br/>
                + <b>Python:</b> %s
                &nbsp;&nbsp;&nbsp;
                + <b>PyQt5:</b> %s
                &nbsp;&nbsp;&nbsp;
                + <b>SIP:</b> %s
            </p>
            <p style="font-size:13px;">
                Copyright &copy; 2017 <a href="mailto:pete@ozmartians.com">Pete Alexandrou</a>
                <br/>
                Website: <a href="%s">%s</a>
            </p>
            <p style="font-size:13px;">
                Icon design by <a href="https://github.com/PapirusDevelopmentTeam">Papirus
                Development Team</a>
            </p>
            <p style="font-size:11px;">
                This program is free software; you can redistribute it and/or
                modify it under the terms of the GNU General Public License
                version 3, or (at your option) any later version.
                This software uses libraries from the <a href="https://mpv.io">mpv</a> and
                <a href="https://www.ffmpeg.org">FFmpeg</a> projects under the
                <a href="https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html">LGPLv2.1</a> license.
            </p>
        </td>
    </tr>
</table>''' % (weight, qApp.applicationName(), weight,
               qApp.applicationVersion(), platform.architecture()[0],
               self.parent.parent.mediaPlayer.mpv_version.replace('mpv ', ''),
               linebreak, ffmpeg_version, sys.version.split(' ')[0],
               PYQT_VERSION_STR, SIP_VERSION_STR,
               qApp.organizationDomain(), qApp.organizationDomain()))


class CreditsTab(QTextBrowser):
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
        <br/>
        <div align="center">
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
        </div>''')


class LicenseTab(QTextBrowser):
    def __init__(self):
        super(LicenseTab, self).__init__()
        self.setObjectName('license')
        self.setSource(QUrl('qrc:/LICENSE.html'))
