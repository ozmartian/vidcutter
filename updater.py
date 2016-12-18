#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from distutils.version import LooseVersion
from urllib.error import HTTPError
from urllib.request import urlopen

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import qApp


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
