#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QBrush, QColor
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QAbstractItemView, QHeaderView


class VideoInfo(QWidget):
    metadata = dict(video=dict(), audio=dict())

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
        self.metadata = dict(video=dict(), audio=dict())
        for prop in VideoInfo.video_props():
            if hasattr(self.mpv, prop):
                self.metadata['video'][prop] = getattr(self.mpv, prop)
        for prop in VideoInfo.audio_props():
            if hasattr(self.mpv, prop):
                self.metadata['audio'][prop] = getattr(self.mpv, prop)

    def build_tree(self) -> None:
        self.parse()
        if os.getenv('DEBUG', False):
            self.logger.info(self.metadata)

        def populate_tree(item: QTreeWidgetItem, data):
            item.setExpanded(True)
            if type(data) is dict:
                for key, val in data.items():
                    child = QTreeWidgetItem()
                    child.setText(0, str(key))
                    if type(val) is dict:
                        if key in ('audio', 'video'):
                            child.setForeground(0, QBrush(Qt.white))
                            child.setForeground(1, QBrush(Qt.white))
                            child.setBackground(0, QBrush(QColor('#999')))
                            child.setBackground(1, QBrush(QColor('#999')))
                    else:
                        child.setText(1, str(val) if val is not None else 'Unknown')
                    item.addChild(child)
                    populate_tree(child, val)
            else:
                print(data)

        self.infowidget = QTreeWidget(self)
        self.infowidget.setObjectName('mediainfo')
        self.infowidget.setHeaderLabels(['Property', 'Value'])

        populate_tree(self.infowidget.invisibleRootItem(), self.metadata)

        self.infowidget.resizeColumnToContents(0)
        self.infowidget.resizeColumnToContents(1)
        self.infowidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.infowidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.infowidget.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.infowidget.header().setSectionsMovable(False)
        self.infowidget.setIndentation(0)
        self.infowidget.setAlternatingRowColors(True)
        self.infowidget.setSortingEnabled(True)
        self.infowidget.sortByColumn(0, Qt.AscendingOrder)
        self.infowidget.setAnimated(True)

    @staticmethod
    def video_props() -> list():
        return [
            'video_aspect',
            'video_bitrate',
            'video_codec',
            'video_format',
            'video_frame_info',
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
            'audio_params',
            'audio_samplerate',
            'audio_speed_correction'
        ]
