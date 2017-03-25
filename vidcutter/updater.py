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

from PyQt5.QtCore import QJsonDocument, QObject, QUrl, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class Updater(QObject):
    latestVersion = pyqtSignal(QJsonDocument)

    def __init__(self, parent=None):
        super(Updater, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.api_github_latest = QUrl('https://api.github.com/repos/ozmartian/vidcutter/releases/latest')
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.reply_finished)

    def download(self, url: QUrl) -> None:
        if url.isValid():
            self.manager.get(QNetworkRequest(url))

    def reply_finished(self, reply: QNetworkReply) -> None:
        if reply.error():
            self.logger.error(reply.errorString())
            return
        self.log_request(reply)
        jsondoc = QJsonDocument.fromBinaryData(reply.readAll())
        self.latestVersion.emit(jsondoc)
        reply.deleteLater()

    def log_request(self, reply: QNetworkReply):
        self.logger.info(reply.header(QNetworkRequest.ContentTypeHeader))
        self.logger.info(reply.header(QNetworkRequest.LastModifiedHeader).toString('dd-mm-yyyy hh:mm:ss'))
        # self.logger.info(reply.header(QNetworkRequest.ContentLengthHeader).toULongLong())
        self.logger.info(reply.attribute(QNetworkRequest.HttpStatusCodeAttribute))
        self.logger.info(reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute))

    def latest_release(self) -> None:
        self.download(self.api_github_latest)
