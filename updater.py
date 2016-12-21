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
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import qApp, QMessageBox
from qtawesome import icon


class Updater(QThread):
    updateInstalled = pyqtSignal(bool)

    pypi_api_endpoint = 'https://pypi.python.org/pypi/vidcutter/json'
    github_api_endpoint = 'https://api.github.com/repos/ozmartian/vidcutter/releases/latest'
    latest_release_webpage = 'https://github.com/ozmartian/vidcutter/releases/latest'

    def __init__(self):
        QThread.__init__(self)

    def __del__(self) -> None:
        self.wait()

    @staticmethod
    @pyqtSlot()
    def restart_app():
        os.execl(sys.executable, sys.executable, * sys.argv)

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
            QMessageBox.critical(self, "Error calling an external process",
                                 self.proc.errorString(), buttons=QMessageBox.Cancel)

    def check_latest_github(self) -> None:
        try:
            mbox = UpdaterMsgBox(self)
            res = json.loads(urlopen(self.github_api_endpoint).read().decode('utf-8'))
            if 'tag_name' in res.keys():
                latest_release = str(res['tag_name'])
                if LooseVersion(latest_release) > LooseVersion(qApp.applicationVersion()):
                    mbox.notify_update(version=latest_release, installer=self.install_update)
                    return
            mbox.notify_no_update()
        except HTTPError:
            mbox.notify_no_update()

    def check_latest_pypi(self) -> None:
        try:
            mbox = UpdaterMsgBox(self)
            res = json.loads(urlopen(self.pypi_api_endpoint).read().decode('utf-8'))
            if 'info' in res.keys():
                latest_release = str(res['info']['version'])
                if LooseVersion(latest_release) > LooseVersion(qApp.applicationVersion()):
                    self.updateAvailable.emit(True, latest_release)
                    return
            mbox.notify_no_update()
        except HTTPError:
            mbox.notify_no_update()

    def install_update(self) -> None:
        returncode = self.cmd_exec('x-terminal-emulator', '-title "VidCutter Updater" -e "sudo pip3 install '
                          + '--upgrade vidcutter"')
        mbox = UpdaterMsgBox(self)
        mbox.confirm_update(update_success=returncode)

    def run(self) -> None:
        if getattr(sys, 'frozen', False):
            self.check_latest_github()
        else:
            self.check_latest_pypi()
            

class UpdaterMsgBox(QMessageBox):
    def __init__(self, parent):
        super(UpdaterMsgBox, self).__init__(parent)
        self.parent = parent
        self.setTextFormat(Qt.RichText)

    def setWindowTitle(self, title: str):
        super(UpdaterMsgBox, self).setWindowTitle(title.upper())

    @staticmethod
    def notify_update(version: str, installer) -> QMessageBox:
        mbox = QMessageBox(self.parent)
        mbox.setIconPixmap(qApp.windowIcon().pixmap(64, 64))
        mbox.setWindowTitle('NEW VERSION DETECTED')
        mbox.setText('<table border="0" width="350"><tr><td><h3>%s %s</h3></td></tr></table>'
                     % (qApp.applicationName(), version))
        mbox.setInformativeText('A new version of %s has been detected. Would you like to update now?' % qApp.applicationName())
        install_btn = mbox.addButton('Install Update', QMessageBox.AcceptRole)
        install_btn.setIcon(icon('fa.check', color='#444'))
        install_btn.clicked.connect(installer)
        reject_btn = mbox.addButton('Not Now', QMessageBox.RejectRole)
        reject_btn.setIcon(icon('fa.times', color='#444'))
        mbox.setDefaultButton(install_btn)
        return mbox.exec_()

    def notify_no_update(self) -> None:
        mbox = QMessageBox(self.parent)
        mbox.setIconPixmap(icon('fa.thumbs-up', color='#6A4572').pixmap(64, 64))
        mbox.setWindowTitle('ALREADY RUNNING LATEST VERSION')
        mbox.setText('<table border="0" width="350"><tr><td><h3>%s %s</h3></td></tr></table>'
                     % (qApp.applicationName(), qApp.applicationVersion()))
        mbox.setInformativeText('You are already running the latest version of %s.' % qApp.applicationName())
        mbox.setStandardButtons(QMessageBox.Close)
        mbox.setDefaultButton(QMessageBox.Close)
        mbox.exec_()

    def notify_restart(self) -> None:
        mbox = QMessageBox(self.parent)
        mbox.setIconPixmap(mbox.parent.windowIcon().pixmap(64, 64))
        mbox.setWindowTitle('UPDATE COMPLETE')
        mbox.setText('<table border="0" width="350"><tr><td><p>The application needs to be restarted in order to use '
                     + 'the newly installed version.</p><p>Would you like to restart now?</p></td></tr></table>')
        restart_btn = mbox.addButton('Yes', QMessageBox.AcceptRole)
        restart_btn.setIcon(icon('fa.check', color='#444'))
        restart_btn.clicked.connect(Updater.restart_app)
        reject_btn = mbox.addButton('No', QMessageBox.RejectRole)
        reject_btn.setIcon(icon('fa.times', color='#444'))
        mbox.setDefaultButton(restart_btn)
        return mbox.exec_()

    @pyqtSlot(bool)
    def confirm_update(self, update_success: bool) -> None:
        if update_success:
            if QMessageBox.question(self.parent, 'UPDATE COMPLETE',
                                    '<p>To begin using the newly installed version the application needs to be ' +
                                    'restarted.</p><p>Would you like to restart now?</p>',
                                    buttons=QMessageBox.Yes | QMessageBox.No):
                Updater.restart_app()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide()
        self.deleteLater()
        event.accept()
