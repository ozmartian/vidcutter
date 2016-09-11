#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, qApp


class AboutVideoCutter(QDialog):
    def __init__(self, parent, flags=Qt.WindowTitleHint | Qt.WindowSystemMenuHint):
        super(AboutVideoCutter, self).__init__(parent, flags)
        self.setMinimumWidth(560)
        self.logo = QLabel(pixmap=self.parent().windowIcon().pixmap(120, 120))
        content = '''<style>
    a { color:#441d4e; text-decoration:none; font-weight:bold; }
    a:hover { text-decoration:underline; }
</style>
<h1>%s</h1>
<h3>Version: %s</h3>
<p>Copyright &copy; 2016 <a href="mailto:pete@ozmartians.com">Pete Alexandrou</a></p>
<p style="font-size:13px;">
    A special thanks & acknowledgements to the folks behind <b>PyQt5</b> and <b>FFmpeg</b>
    projects and the Qt crew too, of course.
</p>
<p style="font-size:12px;">
    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.
</p>''' % (qApp.applicationName(), qApp.applicationVersion())
        self.content = QLabel(content)
        self.content.setWordWrap(True)
        self.setWindowIcon(self.parent().windowIcon())
        self.setWindowTitle('About %s' % qApp.applicationName())
        self.setContentsMargins(0, 0, 0, 0)
        self.setModal(True)

        main = QHBoxLayout()
        main.addWidget(self.logo, alignment=Qt.AlignTop)
        main.addSpacing(15)
        main.addWidget(self.content)

        layout = QVBoxLayout()
        layout.addLayout(main)
        layout.addSpacing(10)
        layout.addWidget(QPushButton('Close', cursor=Qt.PointingHandCursor, clicked=self.close), alignment=Qt.AlignRight)

        self.setLayout(layout)
