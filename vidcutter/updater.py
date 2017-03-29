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

import logging
import os
import sys
from pkg_resources import parse_version

from PyQt5.QtCore import QJsonDocument, QObject, QUrl, Qt
from PyQt5.QtGui import QCloseEvent, QDesktopServices, QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import qApp, QDialog, QDialogButtonBox, QLabel, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget


class Updater(QWidget):
    def __init__(self, parent=None):
        super(Updater, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.update_available = False
        self.api_github_latest = QUrl('https://api.github.com/repos/ozmartian/vidcutter/releases/latest')
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.done)

    def get(self, url: QUrl) -> None:
        if url.isValid():
            self.manager.get(QNetworkRequest(url))

    def done(self, reply: QNetworkReply) -> None:
        if os.getenv('DEBUG', False):
            self.log_request(reply)
        if reply.error() != QNetworkReply.NoError:
            self.logger.error(reply.errorString())
            return
        jsondoc = QJsonDocument.fromJson(reply.readAll())
        reply.deleteLater()
        jsonobj = jsondoc.object()
        latest = parse_version(jsonobj['tag_name'].toString())
        current = parse_version(qApp.applicationVersion())
        if latest > current:
            response = '''
                <style>
                    p { min-width: 600px; }
                    h1 { color: #642C68; font-family: 'Futura LT', sans-serif; font-weight: 400; }
                </style>
            '''
            response += '''<h1>A new version is available!</h1>
                              <p style="font-size:15px;">
                                <b>Latest version:</b> %s
                                <br/>
                                <b>Installed version:</b> %s
                              </p>''' % (str(latest), str(current))
            self.update_available = True
        else:
            response = '''
                <style>
                    h1 { color: #642C68; font-family: 'Futura LT', sans-serif; font-weight: 400; }
                </style>
            '''
            response += '''
<h1 style="text-align:right;">You are already running the latest version</h1>
<div align="center" style="margin-left:100px;">
    <table cellpadding="3" cellspacing="1" border="0">
        <tr valign="middle">
            <td style="color:#642C68; font-family: 'Futura LT', sans-serif; font-size:15px; text-align:right;">latest version:</td>
            <td style="color:#000; font-size:15px; font-weight:400;">%s</td>
        </tr>
        <tr valign="middle">
            <td style="color:#642C68; font-family: 'Futura LT', sans-serif; font-size:15px; text-align:right;">installed version:</td>
            <td style="color:#000; font-size:15px; font-weight:400;">%s</td>
        </tr>
    </table>
</div>''' % (str(latest), str(current))
            self.update_available = False
        if os.getenv('DEBUG', False):
            self.logger.info('latest version = %s VS current version = %s' % (str(latest), str(current)))
        mbox = UpdaterMsgBox(parent=self)
        mbox.setText(response)
        mbox.show()

    def check(self) -> None:
        self.get(self.api_github_latest)

    def log_request(self, reply: QNetworkReply) -> None:
        self.logger.info('request made at %s' %
                         reply.header(QNetworkRequest.LastModifiedHeader).toString('dd-MM-yyyy hh:mm:ss'))
        self.logger.info('response: %s (%i)  type: %s' %
                         (reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute).upper(),
                          reply.attribute(QNetworkRequest.HttpStatusCodeAttribute),
                          reply.header(QNetworkRequest.ContentTypeHeader)))


class UpdaterMsgBox(QDialog):
    def __init__(self, parent=None, f=Qt.WindowCloseButtonHint, title='Checking updates...'):
        super(UpdaterMsgBox, self).__init__(parent, f)
        self.parent = parent
        self.setObjectName('updatermsgbox')
        self.releases_url = QUrl('https://github.com/ozmartian/vidcutter/releases/latest')
        self.setWindowModality(Qt.WindowModal)
        self.contentLabel = QLabel(textFormat=Qt.RichText, wordWrap=True)

        layout = QVBoxLayout()
        layout.addWidget(self.contentLabel)
        if self.parent.update_available and sys.platform.startswith('linux'):
            disclaimer = QLabel('''<p>Linux users should always install via their distribution's package manager.
                Packages in formats such as TAR.XZ (Arch Linux), DEB (Ubuntu/Debian) and RPM (Fedora, openSUSE) are
                always produced with every official version released. These can be installed via distribution specific
                channels such as the Arch Linux AUR, Ubuntu LaunchPad PPA, Fedora copr, openSUSE OBS and third party
                repositories There is also an AppImage package available for those unable to get things working.</p>
                <p>More details are available at the VidCutter homepage.</p>''')
            disclaimer.setStyleSheet('font-size:12px; border:1px solid #999; padding:2px 10px;' +
                                     'background:rgba(255, 255, 255, 0.8); margin:10px 5px;')
            disclaimer.setWordWrap(True)
            layout.addWidget(disclaimer)
            layout.addWidget(QLabel('Would you list to visit the <b>VidCutter releases page</b> for more details now?'))

        if self.parent.update_available:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.releases_page)
            buttons.rejected.connect(self.close)
        else:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(self.close)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(buttons)
        buttonLayout.addStretch(1)

        layout.addLayout(buttonLayout)
        self.setLayout(layout)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.setWindowTitle(title)
        self.setMinimumWidth(602)

    def releases_page(self):
        QDesktopServices.openUrl(self.releases_url)

    def setText(self, content: str) -> None:
        self.contentLabel.setText(content)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.deleteLater()
        event.accept()
