#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
#
# copyright © 2018 Pete Alexandrou
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

import os

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QSpacerItem, QVBoxLayout)

from vidcutter.libs.munch import Munch


class StreamSelector(QDialog):
    def __init__(self, streams: Munch, parent=None):
        super(StreamSelector, self).__init__(parent)
        self.parent = parent
        self.streams = streams
        self.setObjectName('streamselector')
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Media streams - {}'.format(os.path.basename(self.parent.currentMedia)))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, self)
        buttons.accepted.connect(self.close)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(self.video())
        layout.addWidget(self.audio())
        layout.addWidget(self.subtitles())
        layout.addWidget(self.metadata())
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setMinimumSize(415, 400)
        self.setFixedSize(self.minimumSizeHint())

    @staticmethod
    def lineSeparator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def video(self) -> QGroupBox:
        framerate = round(eval(self.streams.video.avg_frame_rate), 3)
        ratio = self.streams.video.display_aspect_ratio.split(':')
        ratio = round(int(ratio[0]) / int(ratio[1]), 3)
        videoCheckbox = QCheckBox(self)
        videoCheckbox.setToolTip('Toggle video stream')
        videoCheckbox.setCursor(Qt.PointingHandCursor)
        videoCheckbox.setChecked(True)
        videoCheckbox.stateChanged.connect(lambda: self.updateMapping('video'))
        iconLabel = QLabel(self)
        iconLabel.setPixmap(QPixmap(':images/streams-video.png'))
        iconLabel.setFixedWidth(25)
        videoLabel = QLabel('''
            <b>codec:</b> {codec}
            <br/>
            <b>size:</b> {width} x {height}
            &nbsp;
            <b>ratio:</b> {ratio}
            <br/>
            <b>rate:</b> {framerate} fps
            &nbsp;
            <b>color:</b> {pixfmt}
        '''.format(codec=self.streams.video.codec_long_name,
                   width=self.streams.video.width,
                   height=self.streams.video.height,
                   framerate=framerate,
                   ratio=ratio,
                   pixfmt=self.streams.video.pix_fmt), self)
        videolayout = QHBoxLayout()
        videolayout.setSpacing(15)
        videolayout.addWidget(videoCheckbox)
        videolayout.addSpacing(5)
        videolayout.addWidget(iconLabel)
        videolayout.addSpacing(10)
        videolayout.addWidget(videoLabel)
        videogroup = QGroupBox('Video')
        videogroup.setLayout(videolayout)
        return videogroup

    def audio(self) -> QGroupBox:
        # for stream in self.streams.audio:

        # try:
        #     import objbrowser
        #     objbrowser.browse(stream)
        #     break
        # except:
        #     pass

        audioCheckbox1 = QCheckBox(self)
        audioCheckbox1.setToolTip('Toggle audio stream')
        audioCheckbox1.setCursor(Qt.PointingHandCursor)
        audioCheckbox1.setChecked(True)
        audioCheckbox1.stateChanged.connect(lambda: self.updateMapping('audio-1'))
        iconLabel1 = QLabel(self)
        iconLabel1.setPixmap(QPixmap(':images/streams-audio.png'))
        iconLabel1.setFixedWidth(25)
        audioLabel1 = QLabel('''
            <b>codec:</b> {codec}
            &nbsp;
            <b>lang:</b> {language}
            <br/>
            <b>channels:</b> {channels}
            &nbsp;
            <b>rate:</b> {samplerate}
        '''.format(codec='Advanced Audio Codec (AAC)',
                   language='ENG',
                   channels=6,
                   samplerate='48.0 kHz'), self)
        audioCheckbox2 = QCheckBox(self)
        audioCheckbox2.setToolTip('Toggle audio stream')
        audioCheckbox2.setCursor(Qt.PointingHandCursor)
        audioCheckbox2.setChecked(True)
        audioCheckbox2.stateChanged.connect(lambda: self.updateMapping('audio-2'))
        iconLabel2 = QLabel(self)
        iconLabel2.setPixmap(QPixmap(':images/streams-audio.png'))
        iconLabel2.setFixedWidth(25)
        audioLabel2 = QLabel('''
            <b>codec:</b> {codec}
            &nbsp;
            <b>lang:</b> {language}
            <br/>
            <b>channels:</b> {channels}
            &nbsp;
            <b>rate:</b> {samplerate}
        '''.format(codec='MPEG1 Layer-3 (MP3)',
                   language='ENG',
                   channels=2,
                   samplerate='48.0 kHz'), self)
        audiolayout = QGridLayout()
        audiolayout.setSpacing(10)
        audiolayout.addWidget(audioCheckbox1, 0, 0)
        audiolayout.addItem(QSpacerItem(5, 1), 0, 1)
        audiolayout.addWidget(iconLabel1, 0, 2)
        audiolayout.addItem(QSpacerItem(10, 1), 0, 3)
        audiolayout.addWidget(audioLabel1, 0, 4)
        audiolayout.addWidget(StreamSelector.lineSeparator(), 1, 0, 1, 5)
        audiolayout.addWidget(audioCheckbox2, 2, 0)
        audiolayout.addItem(QSpacerItem(5, 1), 2, 1)
        audiolayout.addWidget(iconLabel2, 2, 2)
        audiolayout.addItem(QSpacerItem(10, 1), 2, 3)
        audiolayout.addWidget(audioLabel2, 2, 4)
        audiolayout.setColumnStretch(4, 1)
        audiogroup = QGroupBox('Audio')
        audiogroup.setLayout(audiolayout)
        return audiogroup

    def subtitles(self) -> QGroupBox:
        return QGroupBox('Subtitles')

    def metadata(self) -> QGroupBox:
        return QGroupBox('Metadata')

    @pyqtSlot(str)
    def updateMapping(self, stream_id: str) -> bool:
        return len(stream_id) > 0
