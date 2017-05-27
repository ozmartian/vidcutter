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

from PyQt5.QtCore import (QCommandLineOption, QCommandLineParser, QDir, QFileInfo, QProcess,
                          QSettings, QSize, QStandardPaths, Qt, pyqtSlot)
from PyQt5.QtGui import QCloseEvent, QContextMenuEvent, QDragEnterEvent, QDropEvent, QIcon, QMouseEvent
from PyQt5.QtWidgets import qApp, QApplication, QMainWindow, QMessageBox, QSizePolicy

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
        self.statusBar().setStyleSheet('border:none;padding:0;margin:0;')
        self.setAcceptDrops(True)
        self.show()
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
        if os.getenv('DEBUG', False):
            print('minimum size set to: %s (%s)' % (self.get_size(self.scale), self.scale))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    @staticmethod
    def get_size(mode: str = 'NORMAL') -> QSize:
        modes = {
            'LOW': QSize(750, 405),
            'NORMAL': QSize(900, 640),
            'HIGH': QSize(1800, 1280)
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
        self.ontop = self.settings.value('alwaysOnTop', False, type=bool)
        if self.ontop:
            self.set_always_on_top(self.ontop)

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
                sys.stderr.write('\nERROR: File not found: %s\n\n' % file_path)
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

    # def restart(self) -> None:
    #     self.cutter.deleteLater()
    #     self.init_cutter()

    @pyqtSlot()
    def reboot(self) -> None:
        self.save_settings()
        qApp.exit(MainWindow.EXIT_CODE_REBOOT)

    def save_settings(self) -> None:
        theme = 'dark' if self.cutter.darkThemeAction.isChecked() else 'light'
        self.settings.setValue('theme', theme)
        if self.cutter.underLabelsAction.isChecked():
            labels = 'under'
        elif self.cutter.noLabelsAction.isChecked():
            labels = 'none'
        else:
            labels = 'beside'
        self.settings.setValue('nativeDialogs', self.cutter.nativeDialogsAction.isChecked())
        self.settings.setValue('alwaysOnTop', self.cutter.alwaysOnTopAction.isChecked())
        self.settings.setValue('keepClips', self.cutter.keepClipsAction.isChecked())
        self.settings.setValue('aspectRatio', 'keep' if self.cutter.keepRatioAction.isChecked() else 'stretch')
        self.settings.setValue('hwdec', 'auto' if self.cutter.hardwareDecodingAction.isChecked() else 'no')
        self.settings.setValue('volume', self.cutter.volumeSlider.value())
        self.settings.setValue('level1Seek', self.cutter.level1_spinner.value())
        self.settings.setValue('level2Seek', self.cutter.level2_spinner.value())
        self.settings.setValue('toolbarLabels', labels)
        self.settings.setValue('timelineThumbs', self.cutter.thumbnailsButton.isChecked())
        self.settings.setValue('enableOSD', self.cutter.osdButton.isChecked())
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        self.settings.sync()

    @pyqtSlot(bool)
    def set_always_on_top(self, flag: bool) -> None:
        if flag:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            if hasattr(self.cutter, 'mediaPlayer'):
                self.cutter.mediaPlayer.ontop = True
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            if hasattr(self.cutter, 'mediaPlayer'):
                self.cutter.mediaPlayer.ontop = False
        self.show()

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
        QMessageBox.critical(self, 'An error occurred', '%s<br/>Please try again or use a valid media file.' % msg,
                             QMessageBox.Ok)
        self.cutter.initMediaControls(False)

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

    def closeEvent(self, event: QCloseEvent) -> None:
        event.accept()
        if hasattr(self, 'cutter'):
            self.save_settings()
            if hasattr(self.cutter, 'mediaPlayer'):
                self.cutter.mediaPlayer.terminate()
        qApp.quit()


def main():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_Use96Dpi'):
        QApplication.setAttribute(Qt.AA_Use96Dpi, True)
    if hasattr(Qt, 'AA_UseStyleSheetPropagationInWidgetStyles'):
        QApplication.setAttribute(Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
    app = QApplication(sys.argv)
    app.setApplicationName('VidCutter')
    app.setApplicationVersion(MainWindow.get_version())
    app.setOrganizationDomain('ozmartians.com')
    app.setQuitOnLastWindowClosed(True)
    win = MainWindow()
    exit_code = app.exec_()
    if exit_code == MainWindow.EXIT_CODE_REBOOT:
        if sys.platform == 'win32':
            QProcess.startDetached('"%s"' % qApp.applicationFilePath())
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
