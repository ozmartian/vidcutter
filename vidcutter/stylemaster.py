#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - a simple yet fast & accurate video cutter & joiner
#
# copyright © 2017 Pete Alexandrou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import qApp, QStyleFactory


class StyleMaster:

    @staticmethod
    def dark():
        qApp.setStyle(QStyleFactory.create('Fusion'))

        darkPalette = QPalette()
        darkPalette.setColor(QPalette.Window, QColor(27, 35, 38))
        darkPalette.setColor(QPalette.WindowText, QColor(234, 234, 234))
        darkPalette.setColor(QPalette.Base, QColor(27, 35, 38))
        darkPalette.setColor(QPalette.AlternateBase, QColor(12, 15, 16))
        darkPalette.setColor(QPalette.ToolTipBase, QColor(234, 234, 234))
        darkPalette.setColor(QPalette.ToolTipText, Qt.white)
        darkPalette.setColor(QPalette.Text, QColor(234, 234, 234))
        darkPalette.setColor(QPalette.Button, QColor(27, 35, 38))
        darkPalette.setColor(QPalette.ButtonText, Qt.white)
        darkPalette.setColor(QPalette.BrightText, QColor(100, 215, 222))
        darkPalette.setColor(QPalette.Link, QColor(126, 71, 130))
        darkPalette.setColor(QPalette.Highlight, QColor(126, 71, 130))
        darkPalette.setColor(QPalette.HighlightedText, Qt.white)

        darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(79, 85, 87))
        darkPalette.setColor(QPalette.Disabled, QPalette.Light, QColor(12, 15, 16))

        qApp.setPalette(darkPalette)

        qApp.setStyleSheet('QToolTip { color:#FFF; background-color:#642C68; border:1px solid #0C0F10; }')
