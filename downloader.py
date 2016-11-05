#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import sys
from urllib.request import urlopen

from PyQt5.QtCore import QFileInfo, QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QMessageBox, QLabel, QProgressBar, QVBoxLayout, qApp

ffmpeg_64bit = 'https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-latest-win64-static.7z'
ffmpeg_32bit = 'https://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-latest-win32-static.7z'

dl_path = os.path.join(QFileInfo(__file__).absolutePath()

class DownloaderUI(QDialog):
    def __init__(self, parent, f=Qt.Dialog):
        super(QDialog, self).__init__(parent, f)
        self.parent = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(485)
        self.setContentsMargins(20, 20, 20, 20)
        layout = QVBoxLayout()
        self.progress_label = QLabel(alignment=Qt.AlignCenter)
        self.progress = QProgressBar(self.parent, minimum=0, maximum=100)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress)
        self.setLayout(layout)
        self.setWindowTitle('Download Progress')

    @pyqtSlot(int)
    def update_progress(self, progress: int) -> None:
        self.progress.setValue(progress)

    @pyqtSlot(str)
    def update_progress_label(self, progress_txt: str) -> None:
        self.progress_label.setText(progress_txt)
        qApp.processEvents()
        self.ensurePolished()

    @pyqtSlot()
    def download_complete(self) -> None:
        qApp.restoreOverrideCursor()
        QMessageBox.information(self.parent, 'Download complete...', QMessageBox.Ok)
        self.close()
        self.deleteLater()


class Downloader(QThread):

    dlComplete = pyqtSignal()
    dlProgress = pyqtSignal(int)
    dlProgressTxt = pyqtSignal(str)

    def __init__(self):
        QThread.__init__(self)
        self.download_link = globals()['ffmpeg_%s' % platform.architecture()[0]]
        self.download_path = dl_path

    def __del__(self) -> None:
        self.wait()

    def download_file(self) -> None:
        conn = urlopen(self.download_link)
        fileSize = int(conn.info()['Content-Length'])
        fileName = os.path.basename(self.download_path)
        downloadedChunk = 0
        blockSize = 2048
        with open(self.download_path, 'wb') as sura:
            while True:
                chunk = conn.read(blockSize)
                if not chunk:
                    break
                downloadedChunk += len(chunk)
                sura.write(chunk)
                progress = float(downloadedChunk) / fileSize
                self.dlProgress.emit(progress * 100)
                progressTxt = '<b>Downloading {0}</b>:<br/>{1} [{2:.2%}] <b>of</b> {3} <b>bytes</b>.'\
                    . format(fileName, downloadedChunk, progress, fileSize)
                self.dlProgressTxt.emit(progressTxt)
        self.dlComplete.emit()

    def run(self) -> None:
        self.download_file()
