#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import signal
import sys

from PyQt5.QtCore import QCommandLineParser, QCommandLineOption, QFileInfo, QTextStream, QFile, QStandardPaths
from PyQt5.QtGui import QCloseEvent, QDropEvent, QDragEnterEvent
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication

from vidcutter.videocutter import VideoCutter

signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.init_logging()
        self.edl, self.video = '', ''
        self.parse_cmdline()
        self.init_cutter()
        self.setWindowTitle('%s' % qApp.applicationName())
        self.setContentsMargins(0, 0, 0, 0)
        self.statusBar().showMessage('Ready')
        self.statusBar().setStyleSheet('border:none;')
        self.setAcceptDrops(True)
        self.setMinimumSize(900, 650)
        self.resize(900, 650)
        self.show()
        try:
            if len(self.video):
                self.cutter.loadMedia(self.video)
            if len(self.edl):
                self.cutter.openEDL(edlfile=self.edl)
        except (FileNotFoundError, PermissionError):
            QMessageBox.critical(self, 'Error loading file', sys.exc_info()[0])
            qApp.restoreOverrideCursor()
            self.cutter.startNew()
        if not self.cutter.ffmpeg_check():
            self.close()
            sys.exit(1)

    def init_logging(self) -> None:
        log_path = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation).lower()
        os.makedirs(log_path, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_path, '%s.log' % qApp.applicationName().lower()),
            level=logging.ERROR)
        logging.captureWarnings(capture=True)

    def parse_cmdline(self) -> None:
        self.parser = QCommandLineParser()
        self.parser.setApplicationDescription('A simple video cutter & joiner')
        self.parser.addPositionalArgument('video', 'Preloads the video file in app.', '[video]')
        self.edl_option = QCommandLineOption('edl', 'Preloads clip index from a previously saved EDL file.\n' +
                                             'NOTE: You must also set the video argument for this to work.', 'edl file')
        self.parser.addOption(self.edl_option)
        self.parser.addVersionOption()
        self.parser.addHelpOption()
        self.parser.process(qApp)
        self.args = self.parser.positionalArguments()
        if self.parser.value('edl').strip() and not os.path.exists(self.parser.value('edl')):
            print('\n    ERROR: EDL file not found.\n', file=sys.stderr)
            self.close()
            sys.exit(1)
        if self.parser.value('edl').strip() and len(self.args) == 0:
            print('\n    ERROR: Video file argument is missing.\n    You must provide a video file argument if ' +
                  'preloading an EDL file.\n', file=sys.stderr)
            self.close()
            sys.exit(1)
        if self.parser.value('edl').strip():
            self.edl = self.parser.value('edl')
        if len(self.args) > 0 and not os.path.exists(self.args[0]):
            print('\n    ERROR: Video file not found.\n', file=sys.stderr)
            self.close()
            sys.exit(1)
        if len(self.args) > 0:
            self.video = self.args[0]

    def init_cutter(self) -> None:
        self.cutter = VideoCutter(self)
        qApp.setWindowIcon(self.cutter.appIcon)
        self.setCentralWidget(self.cutter)

    @staticmethod
    def get_bitness() -> int:
        from struct import calcsize
        return calcsize('P') * 8

    def restart(self) -> None:
        self.cutter.deleteLater()
        self.init_cutter()

    @staticmethod
    def get_path(path: str = None, override: bool = False) -> str:
        if override:
            if getattr(sys, 'frozen', False):
                return os.path.join(sys._MEIPASS, path)
            return os.path.join(QFileInfo(__file__).absolutePath(), path)
        return ':%s' % path

    @staticmethod
    def load_stylesheet(qssfile: str) -> None:
        if QFileInfo(qssfile).exists():
            qss = QFile(qssfile)
            qss.open(QFile.ReadOnly | QFile.Text)
            qApp.setStyleSheet(QTextStream(qss).readAll())

    @staticmethod
    def get_version(filename: str = '__init__.py') -> str:
        with open(MainWindow.get_path(filename, override=True), 'r') as initfile:
            for line in initfile.readlines():
                m = re.match('__version__ *= *[\'](.*)[\']', line)
                if m:
                    return m.group(1)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        filename = event.mimeData().urls()[0].toLocalFile()
        self.cutter.loadMedia(filename)
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        if hasattr(self, 'cutter'):
            self.cutter.deleteLater()
        self.deleteLater()
        qApp.quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('VidCutter')
    app.setApplicationVersion(MainWindow.get_version())
    app.setOrganizationDomain('http://vidcutter.ozmartians.com')
    app.setQuitOnLastWindowClosed(True)
    win = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
