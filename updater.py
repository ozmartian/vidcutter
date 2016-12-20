#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import shlex
import sys
from distutils.version import LooseVersion
from urllib.error import HTTPError
from urllib.request import urlopen

from PyQt5.QtCore import QFileInfo, QProcess, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import qApp,  QMessageBox, QSizePolicy, QSpacerItem
from qtawesome import icon


class Updater(QThread):
    updateAvailable = pyqtSignal(bool, str)
    updateInstalled = pyqtSignal(bool)

    pypi_api_endpoint = 'https://pypi.python.org/pypi/vidcutter/json'
    github_api_endpoint = 'https://api.github.com/repos/ozmartian/vidcutter/releases/latest'
    latest_release_webpage = 'https://github.com/ozmartian/vidcutter/releases/latest'

    def __init__(self, check_only: bool = True):
        QThread.__init__(self)
        self.check_only = check_only

    def __del__(self) -> None:
        self.wait()

    def init_proc(self) -> QProcess:
        proc = QProcess()
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.setWorkingDirectory(self.get_path())
        if hasattr(proc, 'errorOccurred'):
            proc.errorOccurred.connect(self.cmdError)
        return proc

    def cmd_exec(self, cmd: str, args: str = None) -> bool:
        if self.proc.state() == QProcess.NotRunning:
            self.proc.start(cmd, shlex.split(args))
            self.proc.waitForFinished(-1)
            if self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0:
                return True
        return False

    def get_path(self) -> str:
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return QFileInfo(__file__).absolutePath()

    @pyqtSlot(QProcess.ProcessError)
    def cmdError(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.Crashed:
            QMessageBox.critical(self, "Error calling an external process",
                                 self.proc.errorString(), buttons=QMessageBox.Cancel)

    def check_latest_github(self) -> None:
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

    def check_latest_pypi(self) -> None:
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

    def install_update(self) -> None:
        if sys.platform == 'win32':
            pass
        else:
            self.proc = self.init_proc()
            self.cmd_exec('x-terminal-emulator', '--hold -title "VidCutter Updater" -e "sudo pip3 install '
                          + '--upgrade vidcutter"')

    def run(self) -> None:
        if self.check_only:
            if sys.platform == 'win32':
                self.check_latest_github()
            else:
                self.check_latest_pypi()
        else:
            self.install_update()


class UpdaterMsgBox(QMessageBox):
    def __init__(self, parent):
        super(UpdaterMsgBox, self).__init__(parent)
        self.parent = parent
        self.setTextFormat(Qt.RichText)

    def setWindowTitle(self, title: str):
        super(UpdaterMsgBox, self).setWindowTitle(title.upper())

    def notify_update(self, version: str) -> QMessageBox:
        self.setIconPixmap(self.parent.windowIcon().pixmap(64, 64))
        self.setDefaultButton(UpdaterMsgBox.Yes)
        self.setWindowTitle('NEW VERSION DETECTED')
        self.setText('<table border="0" width="350"><tr><td><h3>%s %s</h3></td></tr></table>'
                     % (qApp.applicationName(), version))
        self.setInformativeText('A new version of %s has been detected.' % qApp.applicationName())
        install_btn = self.addButton('Install Update', UpdaterMsgBox.AcceptRole)
        install_btn.setIcon(icon('fa.check', color='#444'))
        install_btn.clicked.connect(self.install_update)
        reject_btn = self.addButton('Cancel', UpdaterMsgBox.RejectRole)
        reject_btn.setIcon(icon('fa.times', color='#444'))
        return self.exec_()

    def notify_no_update(self) -> None:
        self.setIconPixmap(icon('fa.thumbs-up', color='#6A4572').pixmap(64, 64))
        self.setStandardButtons(UpdaterMsgBox.Ok)
        self.setWindowTitle('ALREADY RUNNING LATEST VERSION')
        self.setText('<table border="0" width="350"><tr><td><h3>%s %s</h3></td></tr></table>'
                     % (qApp.applicationName(), qApp.applicationVersion()))
        self.setInformativeText('You are already running the latest version of %s.' % qApp.applicationName())
        self.setStandardButtons(UpdaterMsgBox.Ok)
        self.setDefaultButton(UpdaterMsgBox.Ok)
        self.exec_()

    @pyqtSlot()
    def install_update(self) -> None:
        self.updater = Updater(check_only=False)
        self.updater.updateInstalled.connect(self.confirm_update)
        self.updater.start()

    @pyqtSlot(bool)
    def confirm_update(self, update_success: bool) -> None:
        print('updater outcome = %s' % str(update_success))

    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide()
        self.deleteLater()
