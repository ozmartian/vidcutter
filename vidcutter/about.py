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

import logging
import sys
from datetime import datetime

from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import QFile, QObject, QSize, QTextStream, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QStyleFactory,
                             QTabWidget, QVBoxLayout, QWidget, qApp)

from vidcutter.libs.config import cached_property

import vidcutter


class About(QDialog):
    def __init__(self, ffmpeg_service: QObject, mpv_service: QObject, parent: QWidget):
        super(About, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.ffmpeg_service = ffmpeg_service
        self.mpv_service = mpv_service
        self.theme = self.parent.theme
        self.setObjectName('aboutwidget')
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowFlags(Qt.Window | Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setWindowModality(Qt.ApplicationModal)
        logolabel = QLabel(self)
        logolabel.setPixmap(QPixmap(':/images/about-logo.png'))
        versionlabel = QLabel('''
            <style>
                b.label {{
                    font-family: "Noto Sans", sans-serif;
                    font-size: 14px;
                    font-weight: 500;
                    color: {0};
                }}
                b.version {{
                    font-family: "Futura LT", sans-serif;
                    font-size: 16px;
                    font-weight: 600;
                }}
            </style>
            <b class="label">version:</b>&nbsp; <b class="version">{1}</b>
        '''.format('#EA95FF' if self.theme == 'dark' else '#441D4E', qApp.applicationVersion(), self))
        if self.parent.parent.flatpak:
            versionlabel.setText(versionlabel.text() + ' <span style="font-size:12px;">- FLATPAK</span>')
            versionspacing = 75
        else:
            versionspacing = 95
        versionlabel.setAlignment(Qt.AlignBottom)
        versionlayout = QHBoxLayout()
        versionlayout.setSpacing(0)
        versionlayout.setContentsMargins(0, 0, 0, 0)
        versionlayout.addStretch(1)
        versionlayout.addWidget(versionlabel)
        versionlayout.addSpacing(versionspacing)
        headerlayout = QVBoxLayout()
        headerlayout.setSpacing(0)
        headerlayout.setContentsMargins(0, 0, 0, 0)
        headerlayout.addWidget(logolabel, 1)
        headerlayout.addLayout(versionlayout)
        self.tab_about = AboutTab(self)
        self.tab_credits = CreditsTab(self)
        self.tab_license = LicenseTab(self)
        scrollarea = QScrollArea(self)
        scrollarea.setStyleSheet('QScrollArea { background:transparent; }')
        scrollarea.setWidgetResizable(True)
        scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollarea.setFrameShape(QScrollArea.NoFrame)
        scrollarea.setWidget(self.tab_license)
        if sys.platform in {'win32', 'darwin'}:
            scrollarea.setStyle(QStyleFactory.create('Fusion'))
        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tabs.addTab(self.tab_about, 'About')
        tabs.addTab(self.tab_credits, 'Credits')
        tabs.addTab(scrollarea, 'License')
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.close)
        layout = QVBoxLayout()
        layout.addLayout(headerlayout)
        layout.addWidget(tabs, 1)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setWindowTitle('About {}'.format(qApp.applicationName()))
        self.setFixedSize(self.sizeHint())

    def sizeHint(self) -> QSize:
        modes = {
            'LOW': QSize(450, 300),
            'NORMAL': QSize(500, 510 if sys.platform == 'darwin' else 490),
            'HIGH': QSize(1080, 920)
        }
        return modes[self.parent.parentWidget().scale]


class BaseTab(QLabel):
    def __init__(self, parent=None):
        super(BaseTab, self).__init__(parent)
        self.setTextFormat(Qt.RichText)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setOpenExternalLinks(True)
        if parent.theme == 'dark':
            bgcolor = 'rgba(12, 15, 16, 210)'
            pencolor = '#FFF'
        else:
            bgcolor = 'rgba(255, 255, 255, 200)'    
            pencolor = '#000'
        self.setStyleSheet('''
            QLabel {{
                background-color: {bgcolor};
                color: {pencolor};
                padding: 8px;
            }}'''.format(**locals()))


# noinspection PyBroadException
class AboutTab(BaseTab):
    def __init__(self, parent):
        super(AboutTab, self).__init__(parent)
        self.parent = parent
        self.missing = '<span style="color:maroon; font-weight:bold;">MISSING</span>'
        pencolor = '#FAFAFA' if self.parent.theme == 'dark' else '#222'
        linkcolor = '#EA95FF' if self.parent.theme == 'dark' else '#441D4E'
        mpv_version = self.mpv_version
        ffmpeg_version = self.ffmpeg_version
        python_version = sys.version.split(' ')[0]
        pyqt_version = PYQT_VERSION_STR
        year = datetime.now().year
        mailto = vidcutter.__email__
        author = vidcutter.__author__
        website = vidcutter.__website__
        bugreport = vidcutter.__bugreport__
        self.setText('''
<style>
    table {{ width:100%; font-family:"Noto Sans", sans-serif; background-color:transparent; }}
    td.label {{ font-size:13px; font-weight:bold; text-align:right; }}
    td.value {{
        color: {pencolor};
        font-weight: 600;
        font-family: "Futura LT", sans-serif;
        font-size: 12.5px;
        vertical-align: bottom;
    }}
    a {{ color: {linkcolor}; text-decoration:none; font-weight:bold; }}
</style>
<table border="0" cellpadding="0" cellspacing="4">
    <tr>
        <td>
            <table border="0" cellpadding="0" cellspacing="0">
                <tr valign="top">
                    <td>
                        <table cellpadding="2" cellspacing="0" border="0">
                            <tr>
                                <td class="label">libmpv:</td>
                                <td class="value">{mpv_version}</td>
                                <td width="35" rowspan="2">&nbsp;</td>
                                <td class="label">PyQt:</td>
                                <td class="value">{pyqt_version}</td>
                            </tr>
                            <tr>
                                <td class="label">FFmpeg:</td>
                                <td class="value">{ffmpeg_version}</td>
                                <td class="label">Python:</td>
                                <td class="value">{python_version}</td>
                            </tr>
                        </table>
                        <p style="font-size:13px;">
                            <img src=":/images/copyright.png" style="vertical-align:bottom;" />
                            &nbsp;
                            Copyright {year} <a href="mailto:{mailto}">{author}</a>
                            <br/>
                            <img src=":/images/home.png" style="vertical-align:bottom;" />
                            &nbsp;
                            <a href="{website}">{website}</a>
                        </p>
                        <p style="font-size:13px;">
                            Found a bug? You can <a href="{bugreport}">REPORT IT HERE</a>.
                        </p>
                    </td>
                    <td align="right" nowrap style="font-weight:500;font-size:13px;">
                        <p><b>built using</b></p>
                        <p>
                            <a href="https://python.org" title="Python"><img src=":/images/python.png" /></a>
                            &nbsp;
                            <a href="https://qt.io" title="Qt5"><img src=":/images/qt.png" /></a>
                            <br/><br/>
                            <a href="https://www.jetbrains.com/pycharm" title="PyCharm Professional">
                                <img src=":/images/pycharm.png" />
                            </a>
                        </p>
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
</table>'''.format(**locals()))

    @cached_property
    def mpv_version(self) -> str:
        try:
            return self.parent.mpv_service.version()
        except Exception:
            self.parent.logger.exception('mpv version error', exc_info=True)
            return self.missing

    @cached_property
    def ffmpeg_version(self) -> str:
        try:
            v = self.parent.ffmpeg_service.version()
            return '-'.join(v.replace('~', '-').split('-')[0:2])
        except Exception:
            self.parent.logger.exception('ffmpeg version error', exc_info=True)
            return self.missing


class CreditsTab(BaseTab):
    def __init__(self, parent):
        super(CreditsTab, self).__init__(parent)
        self.parent = parent
        self.setObjectName('credits')
        self.setText('''
        <style>
            table { background-color: transparent; }
            a { color:%s; text-decoration:none; font-weight:bold; }
        </style>
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
                        <a href="http://mpv.io">libmpv</a>
                        -
                        GPLv3+
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
        </table>
        <p>
            Click on a project name for more information from its official website.
        </p>''' % ('#EA95FF' if self.parent.theme == 'dark' else '#441D4E'))


class LicenseTab(BaseTab):
    def __init__(self, parent):
        super(LicenseTab, self).__init__(parent)
        self.setObjectName('license')
        licensefile = QFile(':/license.html')
        licensefile.open(QFile.ReadOnly | QFile.Text)
        content = QTextStream(licensefile).readAll()
        self.setText(content)
        if sys.platform in {'win32', 'darwin'}:
            self.setStyle(QStyleFactory.create('Fusion'))
