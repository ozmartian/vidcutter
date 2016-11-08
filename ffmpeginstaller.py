#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
from urllib.request import urlopen
from zipfile import ZipFile

from PyQt5.QtCore import QFileInfo, QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QMessageBox, QLabel, QProgressBar, QVBoxLayout, qApp

ffmpeg_64bit = 'http://vidcutter.ozmartians.com/support/ffmpeg-win32/x64/ffmpeg.zip'
ffmpeg_32bit = 'http://vidcutter.ozmartians.com/support/ffmpeg-win32/x86/ffmpeg.zip'


class InstallerUI(QDialog):
    def __init__(self, parent, f=Qt.WindowCloseButtonHint):
        super(QDialog, self).__init__(parent, f)
        self.parent = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(485)
        self.setContentsMargins(20, 20, 20, 20)
        layout = QVBoxLayout()
        self.progress_label = QLabel(alignment=Qt.AlignCenter, text='Starting download of FFmpeg...')
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
    def install_complete(self, success: bool = False, error: object = None) -> None:
        qApp.restoreOverrideCursor()
        if success:
            QMessageBox.information(self.parent, 'FFmpeg installation has successfully completed...', QMessageBox.Ok)
        else:
            if error is not None:
                print(str(error))
            QMessageBox.critical(self.parent, 'FFmpeg Installation Error', self.error_content)
            qApp.quit()
        self.close()
        self.deleteLater()


class Installer(QThread):

    installation_complete = pyqtSignal(bool, object)
    update_progressint = pyqtSignal(int)
    update_progresstxt = pyqtSignal(str)

    def __init__(self):
        QThread.__init__(self)
        self.zip_install = globals()['ffmpeg_%s' % platform.architecture()[0]]
        self.install_path = os.path.join(QFileInfo(__file__).absolutePath(), 'bin')
        self.error = None

    def __del__(self) -> None:
        self.wait()

    def download(self) -> bool:
        # try:
        if not os.path.exists(self.install_path):
            os.mkdir(self.install_path)
        conn = urlopen(self.zip_install)
        fileSize = int(conn.info()['Content-Length'])
        fileName = 'ffmpeg.zip'
        downloadedChunk = 0
        blockSize = 1024
        with open(self.install_path, 'wb') as sura:
            while True:
                chunk = conn.read(blockSize)
                if not chunk:
                    break
                downloadedChunk += len(chunk)
                sura.write(chunk)
                progress = float(downloadedChunk) / fileSize
                self.update_progressint.emit(progress * 100)
                progressTxt = '<b>Downloading {0}</b>:<br/>{1} <b>of</b> {2} <b>bytes</b> [{3:.3%}]'\
                    . format(fileName, downloadedChunk, fileSize, progress)
                self.update_progresstxt.emit(progressTxt)
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
        if self.download() and self.install():
            self.installation_complete.emit(True, None)
