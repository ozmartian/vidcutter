#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGridLayout, QLabel, QSizePolicy, QStackedLayout, QStackedWidget, QWidget

from vidcutter.videoslider import VideoSlider
from vidcutter.libs.graphicseffects import OpacityEffect


class VideoSliderWidget(QStackedWidget):
    def __init__(self, parent, slider: VideoSlider):
        super(VideoSliderWidget, self).__init__(parent)
        self.parent = parent
        self.slider = slider
        self.loaderEffect = OpacityEffect()
        self.loaderEffect.setEnabled(False)
        self.setGraphicsEffect(self.loaderEffect)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout().setStackingMode(QStackedLayout.StackAll)
        self.genlabel = QLabel(self.parent)
        self.genlabel.setContentsMargins(0, 0, 0, 14)
        self.genlabel.setPixmap(QPixmap(':/images/generating-thumbs.png'))
        self.genlabel.setAlignment(Qt.AlignCenter)
        self.genlabel.hide()
        sliderLayout = QGridLayout()
        sliderLayout.setContentsMargins(0, 0, 0, 0)
        sliderLayout.setSpacing(0)
        sliderLayout.addWidget(self.slider, 0, 0)
        sliderLayout.addWidget(self.genlabel, 0, 0)
        sliderWidget = QWidget(self.parent)
        sliderWidget.setLayout(sliderLayout)
        self.addWidget(sliderWidget)

    def setLoader(self, enabled: bool=True) -> None:
        if hasattr(self.parent, 'toolbar') and self.parent.mediaAvailable:
            self.parent.toolbar.setEnabled(not enabled)
        self.slider.setEnabled(not enabled)
        self.loaderEffect.setEnabled(enabled)
        if self.parent.mediaAvailable:
            self.genlabel.setVisible(enabled)

    def hideThumbs(self) -> None:
        if self.count() == 3:
            self.widget(2).hide()
            self.widget(1).hide()
            self.slider.thumbnailsOn = False
            self.slider.initStyle()
