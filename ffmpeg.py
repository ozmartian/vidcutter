#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import sys
import traceback
from urllib.request import urlopen
from zipfile import ZipFile

from PyQt5.QtCore import QFileInfo, QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QMessageBox, QLabel, QProgressBar, QVBoxLayout, qApp

ffmpeg_64bit = 'https://github.com/ozmartian/vidcutter/raw/master/bin/x64/ffmpeg.zip'
ffmpeg_32bit = 'https://github.com/ozmartian/vidcutter/raw/master/bin/x86/ffmpeg.zip'


class FFmpegInstallerUI(QDialog):
    def __init__(self, parent, f=Qt.Dialog):
        super(QDialog, self).__init__(parent, f)
        self.parent = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(485)
        self.setContentsMargins(20, 20, 20, 20)
        layout = QVBoxLayout()
        self.progress_label = QLabel(alignment=Qt.AlignCenter)
        self.progress = QProgressBar(self, minimum=0, maximum=100)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress)
        self.setLayout(layout)
        self.setWindowTitle('FFmpeg Install Progress')
        self.error_content = '''<p>Could not complete installation of the FFmpeg tool. Please ensure your online
                                connection is working and that you responded correctly to the Windows administrative
                                prompt when prompted to allow the installation to proceed.</p><p>You can try
                                manually installing this yourself by following the simple instructions available on
                                the %s website:</p><p><b><a href=%s>%s</a></b></p>'''\
                             % (qApp.applicationName(), qApp.organizationDomain(), qApp.organizationDomain())

    @pyqtSlot(int)
    def update_progress(self, progress: int) -> None:
        self.progress.setValue(progress)

    @pyqtSlot(str)
    def update_progress_label(self, progress_txt: str) -> None:
        self.progress_label.setText(progress_txt)
        qApp.processEvents()

    @pyqtSlot(bool)
    def install_complete(self, success: bool = False, error: (BaseException, Exception, traceback) = None) -> None:
        qApp.restoreOverrideCursor()
        if success:
            QMessageBox.information(parent, 'FFmpeg installation complete...', QMessageBox.Ok)
        else:
            if error is not None:
                print(str(error))
            QMessageBox.critical(parent, 'FFmpeg Install Error', self.error_content)
            qApp.quit()
        self.close()
        self.deleteLater()


class FFmpegInstaller(QThread):

    dlcomplete_signal = pyqtSignal(bool, object)
    progressnum_signal = pyqtSignal(int)
    progresstxt_signal = pyqtSignal(str)

    def __init__(self):
        QThread.__init__(self)
        self.zip_install = globals()['ffmpeg_%s' % platform.architecture()[0]]
        self.install_path = os.path.join(QFileInfo(__file__).absolutePath(), 'bin')
        self.error = None

    def __del__(self) -> None:
        self.wait()

    def download(self) -> bool:
        # try:
        conn = urlopen(self.zip_install)
        fileSize = int(conn.info()['Content-Length'])
        fileName = os.path.basename(os.path.join(self.install_path, 'ffmpeg.exe'))
        downloadedChunk = 0
        blockSize = 2048
        with open(self.install_path, 'wb') as sura:
            while True:
                chunk = conn.read(blockSize)
                if not chunk:
                    break
                downloadedChunk += len(chunk)
                sura.write(chunk)
                progress = float(downloadedChunk) / fileSize
                self.progressnum_signal.emit(progress * 100)
                progressTxt = '<b>Downloading {0}</b>:<br/>{1} [{2:.2%}] <b>of</b> {3} <b>bytes</b>.'\
                    . format(fileName, downloadedChunk, progress, fileSize)
                self.progresstxt_signal.emit(progressTxt)
        return True
        # except:
        #     self.error = sys.exc_info()
        #     return False

    def install(self) -> bool:
        # try:
        self.progresstxt_signal.emit('Installing file on your system')
        with ZipFile(os.path.join(self.install_path, 'ffmpeg.zip')) as archive:
            archive.extract('ffmpeg.exe', path=self.install_path)
        return QFileInfo('%s/ffmpeg.exe' % self.install_path).isExecutable()
        # except:
        #     self.error = sys.exc_info()
        #     return False

    def run(self) -> None:
        self.dlcomplete_signal.emit(self.download() and self.install(), self.error)
