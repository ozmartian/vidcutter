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

from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest


class Updater(QObject):
    def __init__(self, parent=None, **kwargs):
        super(Updater, self).__init__(parent, **kwargs)
        self.api_github_latest = QUrl('https://api.github.com/repos/ozmartian/vidcutter/releases/latest')
        self.netman = QNetworkAccessManager()

    def latest_release(self) -> str:
