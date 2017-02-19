#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QCloseEvent, QTextDocument
from PyQt5.QtWidgets import QDialog, QTabWidget, QDialogButtonBox, QVBoxLayout, qApp, QTextBrowser


class AboutVC(QDialog):
    def __init__(self, parent=None, f=Qt.WindowCloseButtonHint):
        super(AboutVC, self).__init__(parent, f)
        self.parent = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.tab_about = AboutTab()
        self.tab_credits = CreditsTab()
        self.tab_license = LicenseTab()
        tabs = QTabWidget()
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
        self.resize(700, 450)

    def closeEvent(self, event: QCloseEvent):
        self.tab_about.deleteLater()
        self.tab_credits.deleteLater()
        self.tab_license.deleteLater()
        self.deleteLater()
        event.accept()


class AboutTab(QTextBrowser):
    def __init__(self):
        super(AboutTab, self).__init__()
        self.setObjectName('aboutapp')
        self.setHtml('''<style>
    a { color:#441d4e; text-decoration:none; font-weight:bold; }
    a:hover { text-decoration:underline; }
    table { width: 100%%; }
</style>
<table border="0" cellpadding="6" cellspacing="10">
    <tr>
        <td>
            <img src=":/images/vidcutter.png" />
        </td>
        <td>
            <p style="font-size:32pt; font-weight:600; color:#6A4572;">%s</p>
            <p>
                <span style="font-size:13pt;"><b>Version: %s</b></span>
                <span style="font-size:10pt;position:relative;left:5px;">( %s )</span>
            </p>
            <p style="font-size:13px;">
                Copyright &copy; 2017 <a href="mailto:pete@ozmartians.com">Pete Alexandrou</a>
                <br/>
                Website: <a href="%s">%s</a>
            </p>
            <p style="font-size:13px;">
                Thanks to the folks behind the <b>Qt</b>, <b>PyQt</b>, <b>mpv</b> and <b>FFmpeg</b>
                projects for all their hard and much appreciated work.
            </p>
            <p style="font-size:13px;">
                The icon is designed by the fine folks at <a href="https://github.com/PapirusDevelopmentTeam">Papirus
                Development Team</a>.
            </p>
            <p style="font-size:11px;">
                This program is free software; you can redistribute it and/or
                modify it under the terms of the GNU General Public License
                as published by the Free Software Foundation; either version 2
                of the License, or (at your option) any later version.
            </p>
            <p style="font-size:11px;">
                This software uses libraries from the <a href="https://mpv.io">mpv</a> and
                <a href="https://www.ffmpeg.org">FFmpeg</a> projects under the
                <a href="https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html">LGPLv2.1</a>
            </p>
        </td>
    </tr>
</table>''' % (qApp.applicationName(), qApp.applicationVersion(), platform.architecture()[0],
               qApp.organizationDomain(), qApp.organizationDomain()))


class CreditsTab(QTextBrowser):
    def __init__(self):
        super(CreditsTab, self).__init__()
        self.setObjectName('credits')
        self.setHtml('''<style>ul { margin-left:-10px; text-align: center; list-style-type: none; }
        li { margin-bottom: 10px; }</style>
    <div>
        <h3 style="text-align:center;">CREDITS &amp; ACKNOWEDGEMENTS</h3>
        <p>
            This application either uses code and tools from the following projects in part or in their entirety as
            deemed permissable by each project's open-source license.
        </p>
        <ul>
            <li>&nbsp;
                <a href="http://ffmpeg.org">FFmpeg</a>
                -
                GPLv2+
            </li>
            <li>&nbsp;
                <a href="http://mpv.io">mpv</a>
                -
                GPLv2+
            </li>
            <li>&nbsp;
                <a href="https://mpv.srsfckn.biz">libmpv</a>
                -
                GPLv3+
                <br/>
                (Windows builds)
            </li>
            <li>&nbsp;
                <a href="https://github.com/jaseg/python-mpv">python-mpv</a>
                -
                AGPLv3
            </li>
            <li>&nbsp;
                <a href="https://www.riverbankcomputing.com/software/pyqt">PyQt5</a>
                -
                GPLv3
            </li>
            <li>&nbsp;
                <a href="https://www.qt.io">Qt5</a>
                -
                LGPLv3
            </li>
        </ul>
    </div>''')


class LicenseTab(QTextBrowser):
    def __init__(self):
        super(LicenseTab, self).__init__()
        self.setObjectName('license')
        self.setSource(QUrl('qrc:/LICENSE.html'))
