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
import logging.handlers
import os
import re
import signal
import sys
import traceback

from PyQt5.QtCore import (QCommandLineOption, QCommandLineParser, QDir, QFile, QFileInfo, QStandardPaths, Qt,
                          QTextStream)
from PyQt5.QtGui import QCloseEvent, QContextMenuEvent, QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap
from PyQt5.QtWidgets import qApp, QApplication, QLabel, QMainWindow, QMessageBox

from vidcutter.videocutter import VideoCutter

signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.edl, self.video = '', ''
        self.parse_cmdline()
        self.init_logger()
        self.init_cutter()
        self.setWindowTitle('%s' % qApp.applicationName())
        self.setContentsMargins(0, 0, 0, 0)
        self.statusBar().showMessage('Ready')
        statuslogo = QLabel(pixmap=QPixmap(':/images/vidcutter-emboss.png'), objectName='logowidget')
        self.statusBar().addPermanentWidget(statuslogo)
        self.statusBar().setStyleSheet('border:none;')
        self.setAcceptDrops(True)
        self.setMinimumSize(900, 640)
        self.show()
        try:
            if len(self.video):
                self.cutter.loadMedia(self.video)
            if len(self.edl):
                self.cutter.openEDL(edlfile=self.edl)
        except (FileNotFoundError, PermissionError) as e:
            QMessageBox.critical(self, 'Error loading file', sys.exc_info()[0])
            logging.exception('Error loading file')
            qApp.restoreOverrideCursor()
            self.cutter.startNew()
        if not self.cutter.ffmpeg_check():
            self.close()
            sys.exit(1)

    def init_logger(self) -> None:
        try:
            log_path = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation).lower()
        except AttributeError:
            if sys.platform == 'win32':
                log_path = os.path.join(QDir.homePath(), 'AppData', 'Local', qApp.applicationName().lower())
            elif sys.platform == 'darwin':
                log_path = os.path.join(QDir.homePath(), 'Library', 'Preferences', qApp.applicationName()).lower()
            else:
                log_path = os.path.join(QDir.homePath(), '.config', qApp.applicationName()).lower()

        os.makedirs(log_path, exist_ok=True)
        handlers = [logging.handlers.RotatingFileHandler(os.path.join(log_path, '%s.log'
                                                                      % qApp.applicationName().lower()),
                                                         maxBytes=1000000, backupCount=1)]
        if os.getenv('DEBUG', False):
            handlers.append(logging.StreamHandler())
        logging.basicConfig(handlers=handlers,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M',
                            level=logging.INFO)
        logging.captureWarnings(capture=True)
        sys.excepthook = self.log_uncaught_exceptions

    @staticmethod
    def log_uncaught_exceptions(cls, exc, tb) -> None:
        logging.critical(''.join(traceback.format_tb(tb)))
        logging.critical('{0}: {1}'.format(cls, exc))

    def parse_cmdline(self) -> None:
        self.parser = QCommandLineParser()
        self.parser.setApplicationDescription('The simply FAST & ACCURATE video cutter & joiner')
        self.parser.addPositionalArgument('video', 'Preloads the video file in app.', '[video]')
        self.edl_option = QCommandLineOption('edl', 'Preloads clip index from a previously saved EDL file.\n' +
                                             'NOTE: You must also set the video argument for this to work.', 'edl file')
        self.debug_option = QCommandLineOption(['d', 'debug'], 'Output all info, warnings and errors to the console. ' +
                                               'This will basically output what is being logged to file to the ' +
                                               'console stdout. Mainly useful for debugging problems with your ' +
                                               'system video and/or audio stack and codec configuration.')

        self.parser.addOption(self.edl_option)
        self.parser.addOption(self.debug_option)
        self.parser.addVersionOption()
        self.parser.addHelpOption()
        self.parser.process(qApp)
        self.args = self.parser.positionalArguments()
        if self.parser.value('edl').strip() and not os.path.exists(self.parser.value('edl')):
            print('\n    ERROR: EDL file not found.\n', file=sys.stderr)
            self.close()
            sys.exit(1)
        if self.parser.value('edl').strip() and len(self.args) == 0:
            print('\n    ERROR: Video file argument is missing.\n', file=sys.stderr)
            self.close()
            sys.exit(1)
        if self.parser.value('edl').strip():
            self.edl = self.parser.value('edl')
        if self.parser.isSet(self.debug_option):
            os.environ['DEBUG'] = '1'
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
        with open(MainWindow.get_path(filename, override=True), 'r', encoding='utf-8') as initfile:
            for line in initfile.readlines():
                m = re.match('__version__ *= *[\'](.*)[\']', line)
                if m:
                    return m.group(1)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if event.reason() == QContextMenuEvent.Mouse:
            self.cutter.appMenu.exec_(event.globalPos())
            event.accept()
        super(MainWindow, self).contextMenuEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.cutter.cliplist.clearSelection()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        filename = event.mimeData().urls()[0].toLocalFile()
        self.cutter.loadMedia(filename)
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        if hasattr(self, 'cutter'):
            if hasattr(self.cutter, 'mediaPlayer'):
                self.cutter.mediaPlayer.terminate()
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
