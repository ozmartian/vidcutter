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
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QScrollArea, QSizePolicy, QSpacerItem, QStyleFactory, QVBoxLayout, QWidget)

from vidcutter.libs.munch import Munch
from vidcutter.libs.iso639 import ISO639_2


class StreamSelector(QDialog):
    def __init__(self, streams: Munch, mappings: list, parent=None, flags=Qt.Dialog | Qt.WindowCloseButtonHint):
        super(StreamSelector, self).__init__(parent, flags)
        self.parent = parent
        self.streams = streams
        self.config = mappings
        self.service = self.parent.videoService
        self.setObjectName('streamselector')
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Media streams - {}'.format(os.path.basename(self.parent.currentMedia)))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, self)
        buttons.accepted.connect(self.close)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        if len(self.streams.video):
            layout.addWidget(self.video())
        if len(self.streams.audio):
            layout.addWidget(self.audio())
        if len(self.streams.subtitle):
            layout.addWidget(self.subtitles())
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setMaximumSize(500, 600)

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
        index = self.streams.video.get('index')
        videoCheckbox = QCheckBox(self)
        videoCheckbox.setToolTip('Toggle video stream')
        videoCheckbox.setCursor(Qt.PointingHandCursor)
        videoCheckbox.setChecked(True)
        videoCheckbox.setEnabled(False)
        videoCheckbox.stateChanged.connect(lambda state, idx=index: self.setConfig(idx, state == Qt.Checked))
        iconLabel = QLabel(self)
        iconLabel.setPixmap(QPixmap(':images/{}/streams-video.png'.format(self.parent.theme)))
        iconLabel.setFixedSize(18, 18)
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
        videoLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
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
        audiolayout = QGridLayout()
        audiolayout.setSpacing(15)
        for stream in self.streams.audio:
            index = stream.get('index')
            checkbox = QCheckBox(self)
            checkbox.setToolTip('Toggle audio stream')
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, idx=index: self.setConfig(idx, state == Qt.Checked))
            icon = QLabel(self)
            icon.setPixmap(QPixmap(':images/{}/streams-audio.png'.format(self.parent.theme)))
            icon.setFixedSize(18, 18)
            if hasattr(stream, 'tags') and hasattr(stream.tags, 'language'):
                label = QLabel('''
                    <b>title:</b> {title}
                    <br/>
                    <b>codec:</b> {codec}
                    <br/>
                    <b>lang:</b> {language}
                    &nbsp;
                    <b>channels:</b> {channels}
                    &nbsp;
                    <b>rate:</b> {samplerate} kHz
                '''.format(title=ISO639_2[stream.tags.language],
                           codec=stream.codec_long_name,
                           language=stream.tags.language,
                           channels=stream.channels,
                           samplerate=round(int(stream.sample_rate) / 1000, 1)), self)
            else:
                label = QLabel('''
                    <b>codec:</b> {codec}
                    <br/>
                    <b>channels:</b> {channels}
                    &nbsp;
                    <b>rate:</b> {samplerate} kHz
                '''.format(codec=stream.codec_long_name,
                           channels=stream.channels,
                           samplerate=round(int(stream.sample_rate) / 1000, 1)), self)
            rows = audiolayout.rowCount()
            audiolayout.addWidget(checkbox, rows, 0)
            audiolayout.addItem(QSpacerItem(5, 1), rows, 1)
            audiolayout.addWidget(icon, rows, 2)
            audiolayout.addItem(QSpacerItem(10, 1), rows, 3)
            audiolayout.addWidget(label, rows, 4)
            if self.streams.audio.index(stream) < len(self.streams.audio) - 1:
                audiolayout.addWidget(StreamSelector.lineSeparator(), rows + 1, 0, 1, 5)
        audiolayout.setColumnStretch(4, 1)
        if len(self.streams.audio) > 2:
            audiolayout.setSizeConstraint(QGridLayout.SetMinAndMaxSize)
            widget = QWidget(self)
            widget.setObjectName('audiowidget')
            widget.setStyleSheet('QWidget#audiowidget { background-color: transparent; }')
            widget.setLayout(audiolayout)
            scroll = QScrollArea(self)
            scroll.setStyleSheet('QScrollArea { background-color: transparent; }')
            if sys.platform in {'win32', 'darwin'}:
                scroll.setStyle(QStyleFactory.create('Fusion'))
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setMinimumHeight(165)
            scroll.setWidget(widget)
            scrolllayout = QHBoxLayout()
            scrolllayout.addWidget(scroll)
            audiogroup = QGroupBox('Audio')
            audiogroup.setLayout(scrolllayout)
        else:
            audiogroup = QGroupBox('Audio')
            audiogroup.setLayout(audiolayout)
        return audiogroup

    def subtitles(self) -> QGroupBox:
        subtitlelayout = QGridLayout()
        subtitlelayout.setSpacing(15)
        for stream in self.streams.subtitle:
            index = stream.get('index')
            checkbox = QCheckBox(self)
            checkbox.setToolTip('Toggle subtitle stream')
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, idx=index: self.setConfig(idx, state == Qt.Checked))
            icon = QLabel(self)
            icon.setPixmap(QPixmap(':images/{}/streams-subtitle.png'.format(self.parent.theme)))
            icon.setFixedSize(18, 18)
            label = QLabel('''
                <b>title:</b> {title}
                <br/>
                <b>lang:</b> {language}
                &nbsp;
                <b>codec:</b> {codec}
            '''.format(title=ISO639_2[stream.tags.language],
                       language=stream.tags.language,
                       codec=stream.codec_long_name), self)
            rows = subtitlelayout.rowCount()
            subtitlelayout.addWidget(checkbox, rows, 0)
            subtitlelayout.addItem(QSpacerItem(5, 1), rows, 1)
            subtitlelayout.addWidget(icon, rows, 2)
            subtitlelayout.addItem(QSpacerItem(10, 1), rows, 3)
            subtitlelayout.addWidget(label, rows, 4)
            if self.streams.subtitle.index(stream) < len(self.streams.subtitle) - 1:
                subtitlelayout.addWidget(StreamSelector.lineSeparator(), rows + 1, 0, 1, 5)
        subtitlelayout.setColumnStretch(4, 1)
        if len(self.streams.subtitle) > 2:
            subtitlelayout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)
            widget = QWidget(self)
            widget.setObjectName('subtitlewidget')
            widget.setStyleSheet('QWidget#subtitlewidget { background-color: transparent; }')
            widget.setLayout(subtitlelayout)
            scroll = QScrollArea(self)
            scroll.setStyleSheet('QScrollArea { background-color: transparent; }')
            if sys.platform in {'win32', 'darwin'}:
                scroll.setStyle(QStyleFactory.create('Fusion'))
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setMinimumHeight(150)
            scroll.setWidget(widget)
            scrolllayout = QHBoxLayout()
            scrolllayout.addWidget(scroll)
            subtitlegroup = QGroupBox('Subtitles')
            subtitlegroup.setLayout(scrolllayout)
        else:
            subtitlegroup = QGroupBox('Subtitles')
            subtitlegroup.setLayout(subtitlelayout)
        return subtitlegroup

    def setConfig(self, index: int, checked: bool) -> None:
        self.config[index] = checked
