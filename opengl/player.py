#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import locale
import logging
import signal
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import mpv


class Player(QWidget):
    def __init__(self, parent=None, filename=None, **kwargs):
        super(Player, self).__init__(parent)
        if filename is None:
            filename = '/home/ozmartian/Downloads/Dave Chappelles Netflix Special  The Age of Spin   2017.mp4'
        self.init_logging()
        self.filename = filename
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(size_policy.hasHeightForWidth())
        self.setSizePolicy(size_policy)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContentsMargins(0, 0, 0, 0)
        mpv_args = {
            'wid': int(self.winId()),
            'keep-open': 'yes',
            'rebase-start-time': 'no',
            'framedrop': 'no',
            'osd-level': '2',
            'osd-fractions': 'yes',
            'hwdec': 'auto'
        }
        self.player = mpv.MPV(log_handler=self.mpv_log, **mpv_args)
        self.player.pause = True
        self.player.fullscreen = True
        self.resize(800, 600)

        self.player.play(self.filename)

        print('MPV: %s' % self.player.mpv_version)
        print('FFmpeg: %s' % self.player.ffmpeg_version)

    def set_position(self, secs: int):
        self.player.time_pos = float(secs)

    @staticmethod
    def delta2QTime(millisecs: int) -> QTime:
        secs = millisecs / 1000
        return QTime((secs / 3600) % 60, (secs / 60) % 60, secs % 60, (secs * 1000) % 1000)

    def get_duration(self):
        print('Duration: %s' % self.deltaToQTime(self.player.duration * 1000).toString('hh:mm:ss'))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.player.pause = not self.player.pause
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            if self.isFullScreen():
                self.player.fullscreen = False
                self.showNormal()
            else:
                self.player.fullscreen = True
                self.showFullScreen()
        elif event.key() == Qt.Key_D:
            self.get_duration()
        elif event.key() == Qt.Key_T:
            self.player.time_pos = float(120)
        elif event.key() == Qt.Key_M:
            self.player.mute = not self.player.mute
        elif event.key() == Qt.Key_F:
            self.player.estimated_frame_number = 20

    def init_logging(self):
        logging.basicConfig(filename='player.log', level=logging.INFO)

    def get_loglevel(self, level: str) -> int:
        self.loglevels = {
            'NOTSET': 0,
            'DEBUG': 10,
            'INFO': 20,
            'WARN': 30,
            'ERROR': 40,
            'FATAL': 50
        }
        if level not in self.loglevels.keys():
            level = 'NOTSET'
        return self.loglevels[level.upper()]

    def mpv_log(self, loglevel, component, message):
        logging.log(self.get_loglevel(loglevel), msg='MPV log: {}: {}'.format(component, message))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pyqtRemoveInputHook()
    locale.setlocale(locale.LC_NUMERIC, 'C')

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    player = Player(None, sys.argv[1] if len(sys.argv) > 1 else None)
    player.show()

    sys.exit(app.exec_())
