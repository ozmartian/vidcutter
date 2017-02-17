#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QStyleFactory, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout


class VideoInfo(QWidget):
    __metadata = dict(video=dict(), audio=dict())

    def __init__(self, parent, mpv: object):
        super(VideoInfo, self).__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        self.mpv = mpv
        self.build_tree()
        layout = QVBoxLayout()
        layout.addWidget(self.infowidget)
        self.setLayout(layout)
        self.setMinimumSize(650, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setWindowTitle('Media Information  ')
        self.show()

    def parse(self) -> None:
        for prop in VideoInfo.video_props():
            if hasattr(self.mpv, prop):
                self.__metadata['video'][prop] = getattr(self.mpv, prop)
        for prop in VideoInfo.audio_props():
            if hasattr(self.mpv, prop):
                self.__metadata['audio'][prop] = getattr(self.mpv, prop)

    def build_tree(self) -> None:
        self.parse()
        if os.getenv('DEBUG', False):
            self.logger.info(self.__metadata)

        def populate_tree(item: QTreeWidgetItem, value):
            item.setExpanded(True)
            if type(value) is dict:
                for key, val, in value.items():
                    child = QTreeWidgetItem()
                    child.setFont(0, QFont('Open Sans Bold'))
                    child.setText(0, str(key))
                    if type(val) is dict:
                        child.setFirstColumnSpanned(True)
                    else:
                        child.setText(1, str(val) if val is not None else 'Unknown')
                    item.addChild(child)
                    populate_tree(child, val)

        self.infowidget = QTreeWidget(self)
        self.infowidget.setStyle(QStyleFactory.create('Fusion'))
        self.infowidget.setObjectName('mediainfo')
        self.infowidget.setHeaderLabels(['Property', 'Value'])
        self.infowidget.setSortingEnabled(True)
        self.infowidget.setAnimated(True)
        populate_tree(self.infowidget.invisibleRootItem(), self.__metadata)

    @staticmethod
    def video_props() -> list():
        return [
            'video_aspect',
            'video_bitrate',
            'video_codec',
            'video_format',
            'video_frame_info',
            'video_out_params',
            'video_output_levels',
            'video_pan_x',
            'video_pan_y',
            'video_params',
            'video_rotate',
            'video_speed_correction',
            'video_zoom'
        ]

    @staticmethod
    def audio_props() -> list():
        return [
            'audio_bitrate',
            'audio_channels',
            'audio_codec',
            'audio_codec_name',
            'audio_delay',
            'audio_device',
            'audio_device_list',
            'audio_out_detected_device',
            'audio_out_params',
            'audio_params',
            'audio_samplerate',
            'audio_speed_correction'
        ]
