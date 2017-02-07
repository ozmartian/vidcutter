#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import hashlib
import itertools
import json
import locale
import logging
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import traceback

import mpv
from PyQt5.QtCore import*
from PyQt5.QtGui import*
from PyQt5.QtWidgets import*
from vidcutter.videocutter import VideoCutter


class Player(QWidget):
    def __init__(self, parent=None, filename=None, **kwargs):
        super(Player, self).__init__(parent)
        # self.init_logging()
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

    def set_position(self, secs: int):
        self.player.time_pos = float(secs)

    def get_duration(self):
        print('Duration: %s' % VideoCutter.deltaToQTime(self.player.duration * 1000).toString('hh:mm:ss'))

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

    player = Player(None, '/home/ozmartian/Downloads/jeff.ross.presents.roast.battle.s02e06.480p.hdtv.x264.rmteam.mkv')
    player.show()

    sys.exit(app.exec_())
