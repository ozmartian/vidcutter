#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from distutils.version import LooseVersion
from urllib.error import HTTPError
from urllib.request import urlopen

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import qApp, QMessageBox


class Updater(QThread):
    updateAvailable = pyqtSignal(bool, str)

    pypi_api_endpoint = 'https://pypi.python.org/pypi/vidcutter/json'
    github_api_endpoint = 'https://api.github.com/repos/ozmartian/vidcutter/releases/latest'
    latest_release_webpage = 'https://github.com/ozmartian/vidcutter/releases/latest'

    def __init__(self, check_only: bool = True):
        QThread.__init__(self)
        self.check_only = check_only

    def __del__(self):
        self.wait()

    def check_latest_github(self):
        try:
            res = json.loads(urlopen(self.github_api_endpoint).read().decode('utf-8'))
            if 'tag_name' in res.keys():
                latest_release = str(res['tag_name'])
                if LooseVersion(latest_release) > LooseVersion(qApp.applicationVersion()):
                    self.updateAvailable.emit(True, latest_release)
                    return
            self.updateAvailable.emit(False, None)
        except HTTPError:
            self.updateAvailable.emit(False, None)

    def check_latest_pypi(self):
        try:
            res = json.loads(urlopen(self.pypi_api_endpoint).read().decode('utf-8'))
            if 'info' in res.keys():
                latest_release = str(res['info']['version'])
                if LooseVersion(latest_release) > LooseVersion(qApp.applicationVersion()):
                    self.updateAvailable.emit(True, latest_release)
                    return
            self.updateAvailable.emit(False, None)
        except HTTPError:
            self.updateAvailable.emit(False, None)

    def download_latest(self):
        # placeholder for future implementation via PyUpdater
        pass

    def run(self):
        if self.check_only:
            if sys.platform == 'win32':
                self.check_latest_github()
            else:
                self.check_latest_pypi()
        else:
            self.download_latest()


class UpdaterMsgBox(QMessageBox):
    def __init__(self, parent):
        super(UpdaterMsgBox, self).__init__(parent)
        self.mbox = UpdaterMsgBox(self)
        self.setMinimumWidth(500)
        self.setTextFormat(Qt.RichText)
        self.setIconPixmap(qApp.windowIcon().pixmap(64, 64))

    def setWindowTitle(self, title: str):
        super(UpdaterMsgBox, self).setWindowTitle(title.upper())

    def question(self, title, text):
        self.mbox.setStandardButtons(UpdaterMsgBox.Yes | UpdaterMsgBox.No)
        self.mbox.setDefaultButton(UpdaterMsgBox.Yes)
        self.mbox.setWindowTitle('<b>%s</b>'% title)
        self.mbox.setText(text)
        return self.mbox.exec_()

    def information(self, title, text):
        self.mbox.setStandardButtons(UpdaterMsgBox.Ok)
        self.mbox.setWindowTitle('<b>%s</b>' % title)
        self.mbox.setText(text)
        self.mbox.adjustSize()
        self.mbox.exec_()
