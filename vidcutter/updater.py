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
import os
import sys

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import qApp, QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from vidcutter.libs.widgets import VCProgressDialog

try:
    # noinspection PyPackageRequirements
    from simplejson import loads, JSONDecodeError
except ImportError:
    from json import loads, JSONDecodeError


class Updater(QDialog):
    def __init__(self, parent=None, flags=Qt.Dialog | Qt.WindowCloseButtonHint):
        super(Updater, self).__init__(parent, flags)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.api_github_latest = QUrl('https://api.github.com/repos/ozmartian/vidcutter/releases/latest')
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.done)

    def get(self, url: QUrl) -> None:
        if url.isValid():
            self.manager.get(QNetworkRequest(url))

    def done(self, reply: QNetworkReply) -> None:
        if reply.error() != QNetworkReply.NoError:
            self.logger.error(reply.errorString())
            sys.stderr.write(reply.errorString())
            return
        if os.getenv('DEBUG', False):
            self.log_request(reply)
        try:
            jsonobj = loads(str(reply.readAll(), 'utf-8'))
            reply.deleteLater()
            latest = jsonobj.get('tag_name')
            current = qApp.applicationVersion()
            self.mbox.show_result(latest, current)
        except JSONDecodeError:
            self.logger.exception('Updater JSON decoding error', exc_info=True)
            raise

    def check(self) -> None:
        self.mbox = UpdaterMsgBox(self.parent, theme=self.parent.theme)
        self.get(self.api_github_latest)

    def log_request(self, reply: QNetworkReply) -> None:
        self.logger.info('request made at %s' %
                         reply.header(QNetworkRequest.LastModifiedHeader).toString('dd-MM-yyyy hh:mm:ss'))
        self.logger.info('response: %s (%i)  type: %s' %
                         (reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute).upper(),
                          reply.attribute(QNetworkRequest.HttpStatusCodeAttribute),
                          reply.header(QNetworkRequest.ContentTypeHeader)))


class UpdaterMsgBox(QDialog):
    def __init__(self, parent=None, theme: str='light', flags=Qt.Dialog | Qt.WindowCloseButtonHint):
        super(UpdaterMsgBox, self).__init__(parent, flags)
        self.parent = parent
        self.theme = theme
        self.setWindowTitle('{} updates'.format(qApp.applicationName()))
        self.setWindowModality(Qt.ApplicationModal)
        self.setObjectName('updaterdialog')
        self.loading = VCProgressDialog(self.parent)
        self.loading.setText('contacting server')
        self.loading.setMinimumWidth(485)
        self.loading.show()

    def releases_page(self) -> None:
        QDesktopServices.openUrl(self.releases_url)

    def show_result(self, latest: str, current: str) -> None:
        self.releases_url = QUrl('https://github.com/ozmartian/vidcutter/releases/latest')
        update_available = True if latest > current else False
        if self.theme == 'dark':
            pencolor1 = '#C681D5'
            pencolor2 = '#FFF'
        else:
            pencolor1 = '#642C68'
            pencolor2 = '#222'
        content = '''<style>
            h1 {
                text-align: center;
                color: %s;
                font-family: "Futura LT", sans-serif;
                font-weight: normal;
            }
            div {
                border: 1px solid #999;
                color: %s;
            }
            table {
                color: %s;
                margin: 10px 0 0 0;
            }
            td.label {
                font-family: "Futura LT", san-serif;
                font-weight: normal;
                text-align: right;
                font-size: 17px;
            }
            td.value {
                font-family: "Noto Sans", sans-serif;
                color: %s;
                font-weight: 500;
                font-size: 16px;
            }
        </style>''' % (pencolor1, pencolor2, pencolor2, pencolor1)
        if update_available:
            content += '<h1>A new version is available!</h1>'
        else:
            content += '<h1>You are already running the latest version</h1>'
        content += '''
            <table border="0" cellpadding="2" cellspacing="0" align="center">
                <tr>
                    <td class="label">latest:</td>
                    <td class="value">%s</td>
                </tr>
                <tr>
                    <td class="label">installed:</td>
                    <td class="value">%s</td>
                </tr>
            </table>''' % (str(latest), str(current))
        if update_available and sys.platform.startswith('linux'):
            content += '''<div style="font-size: 12px; padding: 2px 10px; margin:10px 5px;">
                Linux users should always install via their distribution's package manager.
                Packages in formats such as TAR.XZ (Arch Linux), DEB (Ubuntu/Debian) and RPM (Fedora, openSUSE) are
                always produced with every official version released. These can be installed via distribution specific
                channels such as the Arch Linux AUR, Ubuntu LaunchPad PPA, Fedora copr, openSUSE OBS and third party
                repositories.
                <br/><br/>
                Alternatively, you should try the AppImage version available to download for those unable to
                get newer updated versions to work. An AppImage should always be available with  produced for every
                update released.
            </div>
            <p align="center">
                Would you like to visit the <b>VidCutter releases page</b> for more details now?
            </p>'''
        if update_available:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.releases_page)
            buttons.rejected.connect(self.close)
        else:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(self.close)
        contentLabel = QLabel(content, self.parent)
        contentLabel.setWordWrap(True)
        contentLabel.setTextFormat(Qt.RichText)
        layout = QVBoxLayout()
        layout.addWidget(contentLabel)
        layout.addWidget(buttons)
        self.loading.close()
        self.loading.deleteLater()
        self.setLayout(layout)
        self.setFixedSize(600, self.sizeHint().height())
        self.show()
