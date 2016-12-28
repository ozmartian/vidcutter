#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shlex
import sys
from distutils.version import LooseVersion
from urllib.error import HTTPError
from urllib.request import urlopen

from PyQt5.QtCore import QFileInfo, QProcess, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import qApp, QMessageBox, QWidget
from qtawesome import icon


class Updater(QThread):
    updateAvailable = pyqtSignal(bool, str)
    # updateInstalled = pyqtSignal(bool)

    pypi_api_endpoint = 'https://pypi.python.org/pypi/vidcutter/json'
    github_api_endpoint = 'https://api.github.com/repos/ozmartian/vidcutter/releases/latest'
    latest_release_webpage = 'https://github.com/ozmartian/vidcutter/releases/latest'

    def __init__(self):
        QThread.__init__(self)

    def __del__(self) -> None:
        self.wait()

    @staticmethod
    def restart_app():
        os.execl(sys.executable, sys.executable, *sys.argv)

    def cmd_exec(self, cmd: str, args: str = None) -> bool:
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.setWorkingDirectory(QFileInfo(__file__).absolutePath())
        if hasattr(self.proc, 'errorOccurred'):
            self.proc.errorOccurred.connect(self.cmdError)
        if self.proc.state() == QProcess.NotRunning:
            self.proc.start(cmd, shlex.split(args))
            self.proc.waitForFinished(-1)
            if self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0:
                return True
        return False

    @pyqtSlot(QProcess.ProcessError)
    def cmdError(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.Crashed:
            QMessageBox.critical(None, "Error calling an external process",
                                 self.proc.errorString(), buttons=QMessageBox.Close)

    def check_latest_github(self) -> None:
        try:
            res = json.loads(urlopen(self.github_api_endpoint).read().decode('utf-8'))
            if 'tag_name' in res.keys():
                latest_release = str(res['tag_name'])
                if LooseVersion(latest_release) > LooseVersion(qApp.applicationVersion()):
                    # self.notify_update(version=latest_release, installer=self.install_update)
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
                    # self.notify_update(version=latest_release, installer=self.install_update)
                    self.updateAvailable.emit(True, latest_release)
                    return
            self.updateAvailable.emit(False, None)
        except HTTPError:
            self.updateAvailable.emit(False, None)

    def install_update(self, parent: QWidget) -> None:
        returncode = self.cmd_exec('x-terminal-emulator', '-title "VidCutter Updater" -e "sudo pip3 install '
                                   + '--upgrade vidcutter"')
        self.confirm_update(parent, returncode)

    def run(self) -> None:
        if getattr(sys, 'frozen', False):
            self.check_latest_github()
        else:
            self.check_latest_pypi()

    @staticmethod
    def notify_update(parent: QWidget, version: str) -> QMessageBox.ButtonRole:
        mbox = QMessageBox(parent)
        mbox.setIconPixmap(qApp.windowIcon().pixmap(64, 64))
        mbox.setWindowTitle('%s UPDATER' % qApp.applicationName())
        mbox.setText('<table border="0" width="350"><tr><td><h4 align="center">Current Version: %s -- New Version: %s'
                     % (qApp.applicationVersion(), version) + '</h4></td></tr></table><br/>')
        mbox.setInformativeText(
            'A new version of %s has been detected. Would you like to update now?' % qApp.applicationName())
        install_btn = mbox.addButton('Install Update', QMessageBox.AcceptRole)
        install_btn.setIcon(icon('fa.check', color='#444'))
        reject_btn = mbox.addButton('Not Now', QMessageBox.RejectRole)
        reject_btn.setIcon(icon('fa.times', color='#444'))
        mbox.setDefaultButton(install_btn)
        return mbox.exec_()

    @staticmethod
    def notify_no_update(parent: QWidget) -> None:
        mbox = QMessageBox(parent)
        mbox.setIconPixmap(icon('fa.thumbs-up', color='#6A4572').pixmap(64, 64))
        mbox.setWindowTitle('%s UPDATER' % qApp.applicationName())
        mbox.setText('<h3 style="color:#6A4572;">%s %s</h3>'
                     % (qApp.applicationName(), qApp.applicationVersion()))
        mbox.setInformativeText('You are already running the latest version.<table width="350"><tr><td></td></tr></table>')
        mbox.setStandardButtons(QMessageBox.Close)
        mbox.setDefaultButton(QMessageBox.Close)
        return mbox.exec_()

    @staticmethod
    def notify_restart(parent: QWidget) -> bool:
        mbox = QMessageBox(parent)
        mbox.setIconPixmap(qApp.windowIcon().pixmap(64, 64))
        mbox.setWindowTitle('%s UPDmboxATER' % qApp.applicationName())
        mbox.setText('<h3 style="color:#6A4572;">INSTALLATION COMPLETE</h3>' +
                     '<table border="0" width="350"><tr><td><p>The application needs to be restarted in order to use ' +
                     'the newly installed version.</p><p>Would you like to restart now?</td></tr></table><br/>')
        restart_btn = mbox.addButton('Yes', QMessageBox.AcceptRole)
        restart_btn.setIcon(icon('fa.check', color='#444'))
        restart_btn.clicked.connect(Updater.restart_app)
        reject_btn = mbox.addButton('No', QMessageBox.RejectRole)
        reject_btn.setIcon(icon('fa.times', color='#444'))
        mbox.setDefaultButton(restart_btn)
        return mbox.exec_()

    @staticmethod
    def confirm_update(parent: QWidget, update_success: bool) -> None:
        if update_success and QMessageBox.question(parent, '%s UPDATER' % qApp.applicationName(),
                                                   '<h3>UPDATE COMPLETE</h3><p>To begin using the newly installed ' +
                                                           'version the application needs to be restarted.</p>' +
                                                           '<p>Would you like to restart now?</p><br/>',
                                                   buttons=(QMessageBox.Yes | QMessageBox.No)):
            Updater.restart_app()
