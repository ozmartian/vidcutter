#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, qApp

from .videocutter import VideoCutter


signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.statusBar().showMessage('Ready')
        self.cutter = VideoCutter(self)
        self.setCentralWidget(self.cutter)
        self.setAcceptDrops(True)
        self.setWindowTitle('%s %s' % (qApp.applicationName(), qApp.applicationVersion()))
        self.setWindowIcon(self.cutter.appIcon)
        self.resize(900, 650)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event):
        filename = event.mimeData().urls()[0].toLocalFile()
        self.cutter.loadFile(filename)
        event.accept()

    def closeEvent(self, event):
        self.cutter.deleteLater()
        self.deleteLater()
        qApp.quit()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName('VideoCutter')
    app.setApplicationVersion('1.0')
    app.setQuitOnLastWindowClosed(True)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
