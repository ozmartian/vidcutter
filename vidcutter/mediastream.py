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

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QCloseEvent, QMouseEvent, QPixmap
from PyQt5.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QMessageBox, QScrollArea, QSizePolicy, QSpacerItem, QStyleFactory, QVBoxLayout, QWidget)

from vidcutter.libs.iso639 import ISO639_2
from vidcutter.libs.videoservice import VideoService


class StreamSelector(QDialog):
    def __init__(self, service: VideoService, parent=None, flags=Qt.Dialog | Qt.WindowCloseButtonHint):
        super(StreamSelector, self).__init__(parent, flags)
        self.service = service
        self.parent = parent
        self.streams = service.streams
        self.config = service.mappings
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

    @staticmethod
    def lineSeparator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setLineWidth(1)
        line.setMidLineWidth(0)
        line.setMinimumSize(0, 2)
        return line

    def video(self) -> QGroupBox:
        framerate = round(eval(self.streams.video.avg_frame_rate), 3)
        ratio = self.streams.video.display_aspect_ratio.split(':')
        ratio = round(int(ratio[0]) / int(ratio[1]), 3)
        icon = QLabel('<img src=":images/{}/streams-video.png" />'.format(self.parent.theme), self)
        label = QLabel('''
            <b>index:</b> {index}
            <br/>
            <b>codec:</b> {codec}
            <br/>
            <b>size:</b> {width} x {height}
            &nbsp;
            <b>ratio:</b> {ratio}
            <br/>
            <b>frame rate:</b> {framerate} fps
            &nbsp;
            <b>color format:</b> {pixfmt}'''.format(index=self.streams.video.index,
                                                    codec=self.streams.video.codec_long_name,
                                                    width=self.streams.video.width,
                                                    height=self.streams.video.height,
                                                    framerate='{0:.2f}'.format(framerate),
                                                    ratio='{0:.2f}'.format(ratio),
                                                    pixfmt=self.streams.video.pix_fmt), self)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        videolayout = QHBoxLayout()
        videolayout.setSpacing(15)
        videolayout.addSpacing(25)
        videolayout.addWidget(icon)
        videolayout.addSpacing(45)
        videolayout.addWidget(label)
        videogroup = QGroupBox('Video')
        videogroup.setLayout(videolayout)
        return videogroup

    def audio(self) -> QGroupBox:
        audiolayout = QGridLayout()
        audiolayout.setSpacing(15)
        for stream in self.streams.audio:
            sameplerate = round(int(stream.sample_rate) / 1000, 1)
            checkbox = StreamSelectorCheckBox(stream.index, 'Toggle audio stream', self)
            icon = StreamSelectorLabel('<img src=":images/{}/streams-audio.png" />'.format(self.parent.theme),
                                       checkbox, True, self)
            labeltext = '<b>index:</b> {}<br/>'.format(stream.index)
            if hasattr(stream, 'tags') and hasattr(stream.tags, 'language'):
                labeltext += '<b>language:</b> {}<br/>'.format(ISO639_2[stream.tags.language])
            labeltext += '<b>codec:</b> {}<br/>'.format(stream.codec_long_name)
            labeltext += '<b>channels:</b> {0} &nbsp; <b>sample rate:</b> {1:.2f} kHz' \
                         .format(stream.channels, sameplerate)
            label = StreamSelectorLabel(labeltext, checkbox, False, self)
            rows = audiolayout.rowCount()
            audiolayout.addWidget(checkbox, rows, 0)
            audiolayout.addItem(QSpacerItem(15, 1), rows, 1)
            audiolayout.addWidget(icon, rows, 2)
            audiolayout.addItem(QSpacerItem(30, 1), rows, 3)
            audiolayout.addWidget(label, rows, 4)
            if self.streams.audio.index(stream) < len(self.streams.audio) - 1:
                audiolayout.addWidget(StreamSelector.lineSeparator(), rows + 1, 0, 1, 5)
        audiolayout.setColumnStretch(4, 1)
        audiogroup = QGroupBox('Audio')
        if len(self.streams.audio) > 2:
            audiolayout.setSizeConstraint(QGridLayout.SetMinAndMaxSize)
            widget = QWidget(self)
            widget.setObjectName('audiowidget')
            widget.setStyleSheet('QWidget#audiowidget { background-color: transparent; }')
            widget.setMinimumWidth(400)
            widget.setLayout(audiolayout)
            scrolllayout = QHBoxLayout()
            scrolllayout.addWidget(StreamSelectorScrollArea(widget, 200, self.parent.theme, self))
            audiogroup.setLayout(scrolllayout)
        else:
            audiogroup.setLayout(audiolayout)
        return audiogroup

    def subtitles(self) -> QGroupBox:
        subtitlelayout = QGridLayout()
        subtitlelayout.setSpacing(15)
        for stream in self.streams.subtitle:
            checkbox = StreamSelectorCheckBox(stream.index, 'Toggle subtitle stream', self)
            icon = StreamSelectorLabel('<img src=":images/{}/streams-subtitle.png" />'.format(self.parent.theme),
                                       checkbox, True, self)
            labeltext = '<b>index:</b> {}<br/>'.format(stream.index)
            if hasattr(stream, 'tags') and hasattr(stream.tags, 'language'):
                labeltext += '<b>language:</b> {}<br/>'.format(ISO639_2[stream.tags.language])
            labeltext += '<b>codec:</b> {}'.format(stream.codec_long_name)
            label = StreamSelectorLabel(labeltext, checkbox, False, self)
            rows = subtitlelayout.rowCount()
            subtitlelayout.addWidget(checkbox, rows, 0)
            subtitlelayout.addItem(QSpacerItem(15, 1), rows, 1)
            subtitlelayout.addWidget(icon, rows, 2)
            subtitlelayout.addItem(QSpacerItem(30, 1), rows, 3)
            subtitlelayout.addWidget(label, rows, 4)
            if self.streams.subtitle.index(stream) < len(self.streams.subtitle) - 1:
                subtitlelayout.addWidget(StreamSelector.lineSeparator(), rows + 1, 0, 1, 5)
        subtitlelayout.setColumnStretch(4, 1)
        subtitlegroup = QGroupBox('Subtitles')
        if len(self.streams.subtitle) > 2:
            subtitlelayout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)
            widget = QWidget(self)
            widget.setObjectName('subtitlewidget')
            widget.setStyleSheet('QWidget#subtitlewidget { background-color: transparent; }')
            widget.setMinimumWidth(400)
            widget.setLayout(subtitlelayout)
            scrolllayout = QHBoxLayout()
            scrolllayout.addWidget(StreamSelectorScrollArea(widget, 170, self.parent.theme, self))
            subtitlegroup.setStyleSheet('QGroupBox { padding-right: 0; }')
            subtitlegroup.setLayout(scrolllayout)
        else:
            subtitlegroup.setLayout(subtitlelayout)
        return subtitlegroup

    @pyqtSlot()
    def closeEvent(self, event: QCloseEvent) -> None:
        # check if all audio streams are off
        idx = [stream.index for stream in self.streams.audio]
        no_audio = len(self.streams.audio) and True not in [self.config[i] for i in idx]
        # check if all subtitle streams are off
        idx = [stream.index for stream in self.streams.subtitle]
        no_subtitles = len(self.streams.subtitle) and True not in [self.config[i] for i in idx]
        # warn user if all audio and/or subtitle streams are off
        if no_audio or no_subtitles:
            if no_audio and not no_subtitles:
                warnsubtext = 'All audio streams have been deselected which will produce a file with <b>NO AUDIO</b> ' \
                              'when you save.'
            elif not no_audio and no_subtitles:
                warnsubtext = 'All subtitle streams have been deselected which will produce a file with ' \
                              '<b>NO SUBTITLES</b> when you save.'
            else:
                warnsubtext = 'All audio and subtitle streams have been deselected which will produce a file ' \
                              'with <b>NO AUDIO</b> and <b>NO SUBTITLES</b> when you save.'
            warntext = '''
                <style>
                    h2 {{
                        color: {};
                        font-family: "Futura LT", sans-serif;
                        font-weight: normal;
                    }}
                </style>
                <table border="0" cellpadding="6" cellspacing="0" width="350">
                    <tr>
                        <td><h2>A friendly configuration warning</h2></td>
                    </tr>
                    <tr>
                        <td>{}</td>
                    </tr>
                    <tr>
                        <td>Are you sure this is what you want?</td>
                    </tr>
                </table>'''.format('#C681D5' if self.parent.theme == 'dark' else '#642C68', warnsubtext)
            warnmsg = QMessageBox(QMessageBox.Warning, 'Warning', warntext, parent=self)
            warnmsg.setIconPixmap(QPixmap(':images/warning.png'))
            warnmsg.addButton('Yes', QMessageBox.YesRole)
            cancelbtn = warnmsg.addButton('No', QMessageBox.RejectRole)
            warnmsg.exec_()
            res = warnmsg.clickedButton()
            if res == cancelbtn:
                event.ignore()
                return
        event.accept()
        self.deleteLater()
        super(StreamSelector, self).closeEvent(event)


class StreamSelectorScrollArea(QScrollArea):
    def __init__(self, widget: QWidget, minHeight: int, theme: str, parent):
        super(StreamSelectorScrollArea, self).__init__(parent)
        if sys.platform in {'win32', 'darwin'}:
            self.setStyle(QStyleFactory.create('Fusion'))
        # noinspection PyUnresolvedReferences
        if parent.parent.parent.stylename == 'fusion' or sys.platform in {'win32', 'darwin'}:
            self.setStyleSheet('''
            QScrollArea {{
                background-color: transparent;
                margin-bottom: 10px;
                border: none;
                border-right: 1px solid {};
            }}'''.format('#4D5355' if theme == 'dark' else '#C0C2C3'))
        else:
            self.setStyleSheet('''
            QScrollArea {{
                background-color: transparent;
                margin-bottom: 10px;
                border: none;
            }}''')
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumHeight(minHeight)
        if widget is not None:
            self.setWidget(widget)


class StreamSelectorCheckBox(QCheckBox):
    def __init__(self, stream_index: int, tooltip: str, parent):
        super(StreamSelectorCheckBox, self).__init__(parent)
        self.parent = parent
        self.setObjectName('streamcheckbox')
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setChecked(self.parent.config[stream_index])
        self.stateChanged.connect(lambda state, index=stream_index: self.updateConfig(index, state == Qt.Checked))

    def updateConfig(self, index: int, checked: bool) -> None:
        self.parent.config[index] = checked


class StreamSelectorLabel(QLabel):
    def __init__(self, text: str, checkbox: StreamSelectorCheckBox, is_icon: bool=False, parent=None):
        super(StreamSelectorLabel, self).__init__(parent)
        self.checkbox = checkbox
        self.setAttribute(Qt.WA_Hover, True)
        self.setText(text)
        self.setToolTip(self.checkbox.toolTip())
        self.setCursor(Qt.PointingHandCursor)
        if is_icon:
            self.setFixedSize(18, 18)
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        else:
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self.checkbox is not None:
            self.checkbox.toggle()
        super(StreamSelectorLabel, self).mousePressEvent(event)
