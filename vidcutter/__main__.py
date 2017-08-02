#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
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

from PyQt5.QtCore import (pyqtSlot, QCommandLineOption, QCommandLineParser, QCoreApplication, QDir, QFileInfo,
                          QProcess, QSettings, QSize, QStandardPaths, Qt)
from PyQt5.QtGui import QCloseEvent, QContextMenuEvent, QDragEnterEvent, QDropEvent, QIcon, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import qApp, QApplication, QMainWindow, QMessageBox, QSizePolicy

from vidcutter.videoconsole import ConsoleHandler, ConsoleWidget
from vidcutter.videocutter import VideoCutter

signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)


class MainWindow(QMainWindow):
    EXIT_CODE_REBOOT = 666

    def __init__(self):
        super(MainWindow, self).__init__()
        self.video, self.devmode = '', False
        self.parse_cmdline()
        self.init_logger()
        self.init_settings()
        self.init_scale()
        self.init_cutter()
        self.setWindowTitle('%s' % qApp.applicationName())
        self.setContentsMargins(0, 0, 0, 0)
        self.statusBar().showMessage('Ready')
        self.statusBar().setStyleSheet('border: none; padding: 0; margin: 0;')
        self.setAcceptDrops(True)
        self.show()
        self.console.setGeometry(int(self.x() - (self.width() / 2)), self.y() + int(self.height() / 3), 750, 300)
        try:
            if len(self.video):
                if QFileInfo(self.video).suffix() == 'vcp':
                    self.cutter.openProject(project_file=self.video)
                else:
                    self.cutter.loadMedia(self.video)
        except (FileNotFoundError, PermissionError) as e:
            QMessageBox.critical(self, 'Error loading file', sys.exc_info()[0])
            logging.exception('Error loading file')
            qApp.restoreOverrideCursor()
            self.restart()
        if not self.cutter.ffmpeg_check():
            qApp.exit(1)

    def init_scale(self) -> None:
        screen_size = qApp.desktop().availableGeometry(-1)
        self.scale = 'LOW' if screen_size.width() <= 1024 else 'NORMAL'
        self.setMinimumSize(self.get_size(self.scale))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    @staticmethod
    def get_size(mode: str = 'NORMAL') -> QSize:
        modes = {
            'LOW': QSize(800, 425),
            'NORMAL': QSize(915, 680),
            'HIGH': QSize(1850, 1300)
        }
        return modes[mode]

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
        self.console = ConsoleWidget(self)
        self.consoleLogger = ConsoleHandler(self.console)
        handlers = [logging.handlers.RotatingFileHandler(os.path.join(log_path, '%s.log'
                                                                      % qApp.applicationName().lower()),
                                                         maxBytes=1000000, backupCount=1),
                    self.consoleLogger]
        if self.parser.isSet(self.debug_option):
            handlers.append(logging.StreamHandler())
        logging.basicConfig(handlers=handlers,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M',
                            level=logging.INFO)
        logging.captureWarnings(capture=True)
        sys.excepthook = self.log_uncaught_exceptions

    def init_settings(self) -> None:
        if sys.platform == 'darwin':
            QSettings.setDefaultFormat(QSettings.IniFormat)
            self.settings = QSettings(self)
        else:
            try:
                settings_path = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation).lower()
            except AttributeError:
                if sys.platform == 'win32':
                    settings_path = os.path.join(QDir.homePath(), 'AppData', 'Local', qApp.applicationName().lower())
                elif sys.platform == 'darwin':
                    settings_path = os.path.join(QDir.homePath(), 'Library', 'Preferences',
                                                 qApp.applicationName()).lower()
                else:
                    settings_path = os.path.join(QDir.homePath(), '.config', qApp.applicationName()).lower()
            os.makedirs(settings_path, exist_ok=True)
            settings_file = '%s.ini' % qApp.applicationName().lower()
            self.settings = QSettings(os.path.join(settings_path, settings_file), QSettings.IniFormat)
        if self.settings.value('geometry') is not None:
            self.restoreGeometry(self.settings.value('geometry'))
        if self.settings.value('windowState') is not None:
            self.restoreState(self.settings.value('windowState'))
        self.theme = self.settings.value('theme', 'light', type=str)
        self.startupvol = self.settings.value('volume', 100, type=int)

    @staticmethod
    def log_uncaught_exceptions(cls, exc, tb) -> None:
        logging.critical(''.join(traceback.format_tb(tb)))
        logging.critical('{0}: {1}'.format(cls, exc))

    def parse_cmdline(self) -> None:
        self.parser = QCommandLineParser()
        self.parser.setApplicationDescription('\nVidCutter - the simplest + fastest video cutter & joiner')
        self.parser.addPositionalArgument('video', 'Preload video file', '[video]')
        self.parser.addPositionalArgument('project', 'Open VidCutter project file (.vcp)', '[project]')
        self.debug_option = QCommandLineOption(['debug'], 'debug mode; verbose console output & logging. ' +
                                               'This will basically output what is being logged to file to the ' +
                                               'console stdout. Mainly useful for debugging problems with your ' +
                                               'system video and/or audio stack and codec configuration.')
        self.dev_option = QCommandLineOption(['dev'], 'developer mode; disables the use of compiled resource files ' +
                                             'so that all app resources & assets are accessed directly from the file ' +
                                             'system allowing you to see UI changes immediately. this typically ' +
                                             'relates to changes made to Qt stylesheets (.qss), layout/templates, ' +
                                             'content includes and images. basically all assets defined in .qrc ' +
                                             'files throughout the codebase.')
        self.parser.addOption(self.debug_option)
        self.parser.addOption(self.dev_option)
        self.parser.addVersionOption()
        self.parser.addHelpOption()
        self.parser.process(qApp)
        self.args = self.parser.positionalArguments()
        if self.parser.isSet(self.debug_option):
            os.environ['DEBUG'] = '1'
        if self.parser.isSet(self.dev_option):
            self.devmode = True
        if len(self.args) > 0:
            file_path = QFileInfo(self.args[0]).absoluteFilePath()
            if not os.path.exists(file_path):
                sys.stderr.write('\nERROR: File not found: %s\n' % file_path)
                self.close()
                sys.exit(1)
            self.video = file_path

    def init_cutter(self) -> None:
        self.cutter = VideoCutter(self)
        self.cutter.errorOccurred.connect(self.errorHandler)
        qApp.setWindowIcon(QIcon(':/images/vidcutter.png'))
        self.setCentralWidget(self.cutter)

    @staticmethod
    def get_bitness() -> int:
        from struct import calcsize
        return calcsize('P') * 8

    @pyqtSlot()
    def reboot(self) -> None:
        self.save_settings()
        qApp.exit(MainWindow.EXIT_CODE_REBOOT)

    def save_settings(self) -> None:
        self.settings.setValue('lastFolder', self.cutter.lastFolder)
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        self.settings.sync()

    @staticmethod
    def get_path(path: str = None, override: bool = False) -> str:
        if override:
            if getattr(sys, 'frozen', False):
                return os.path.join(sys._MEIPASS, path)
            return os.path.join(QFileInfo(__file__).absolutePath(), path)
        return ':%s' % path

    @staticmethod
    def get_version(filename: str = '__init__.py') -> str:
        with open(MainWindow.get_path(filename, override=True), 'r', encoding='utf-8') as initfile:
            for line in initfile.readlines():
                m = re.match('__version__ *= *[\'](.*)[\']', line)
                if m:
                    return m.group(1)

    @pyqtSlot(str)
    def errorHandler(self, msg: str) -> None:
        QMessageBox.critical(self, 'An error occurred', msg, QMessageBox.Ok)
        logging.error(msg)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if event.reason() == QContextMenuEvent.Mouse:
            self.cutter.appMenu.exec_(event.globalPos())
            event.accept()
        super(MainWindow, self).contextMenuEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self.cutter.mediaAvailable:
            self.cutter.cliplist.clearSelection()
            self.cutter.timeCounter.clearFocus()
            self.cutter.frameCounter.clearFocus()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        filename = event.mimeData().urls()[0].toLocalFile()
        self.cutter.loadMedia(filename)
        event.accept()

    def resizeEvent(self, event: QResizeEvent) -> None:
        try:
            if self.cutter.mediaAvailable and self.cutter.thumbnailsButton.isChecked():
                self.cutter.seekSlider.reloadThumbs()
        except AttributeError:
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        event.accept()
        self.console.deleteLater()
        if hasattr(self, 'cutter'):
            self.save_settings()
            if hasattr(self.cutter, 'mpvWidget'):
                self.cutter.mpvWidget.shutdown()
        qApp.quit()


def main():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_Use96Dpi'):
        QCoreApplication.setAttribute(Qt.AA_Use96Dpi, True)
    if hasattr(Qt, 'AA_ShareOpenGLContexts'):
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    if sys.platform == 'darwin':
        QApplication.setStyle('Fusion')

    app = QApplication(sys.argv)
    app.setApplicationName('VidCutter')
    app.setApplicationVersion(MainWindow.get_version())
    app.setOrganizationDomain('ozmartians.com')
    app.setQuitOnLastWindowClosed(True)

    win = MainWindow()
    exit_code = app.exec_()
    if exit_code == MainWindow.EXIT_CODE_REBOOT:
        if sys.platform == 'win32':
            if hasattr(win.cutter, 'mpvWidget'):
                win.close()
            QProcess.startDetached('"%s"' % qApp.applicationFilePath())
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
