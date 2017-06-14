#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
#
# copyright © 2017 Pete Alexandrou
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

import codecs
import os
import re
import sys


class VCSetup:
    here = os.path.abspath(os.path.dirname(__file__))

    @staticmethod
    def get_bitness():
        from struct import calcsize
        return calcsize('P') * 8

    @staticmethod
    def get_library_dirs():
        _dirs = []
        if sys.platform == 'win32':
            _dirs = ['vidcutter/libs/pympv/win%s' % VCSetup.get_bitness()]
        return _dirs

    @staticmethod
    def get_value(varname, filename='vidcutter/__init__.py'):
        with codecs.open(os.path.join(VCSetup.here, filename), encoding='utf-8') as initfile:
            for line in initfile.readlines():
                m = re.match('__%s__ *= *[\'](.*)[\']' % varname, line)
                if m:
                    return m.group(1)

    @staticmethod
    def get_description(filename='README.md'):
        with codecs.open(os.path.join(VCSetup.here, filename), encoding='utf-8') as f:
            file = list(f)
        desc = ''
        for item in file[11: len(file)]:
            desc += item
        return desc

    @staticmethod
    def get_install_requires():
        return ['PyQt5', 'PyOpenGL'] if VCSetup.get_value('packager') == 'pypi' else []

    @staticmethod
    def get_data_files():
        files = []
        if sys.platform.startswith('linux'):
            files = [
                ('/usr/share/icons/hicolor/16x16/apps', ['data/icons/hicolor/16x16/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/22x22/apps', ['data/icons/hicolor/22x22/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/24x24/apps', ['data/icons/hicolor/24x24/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/32x32/apps', ['data/icons/hicolor/32x32/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/48x48/apps', ['data/icons/hicolor/48x48/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/64x64/apps', ['data/icons/hicolor/64x64/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/128x128/apps', ['data/icons/hicolor/128x128/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/256x256/apps', ['data/icons/hicolor/256x256/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/512x512/apps', ['data/icons/hicolor/512x512/apps/vidcutter.png']),
                ('/usr/share/icons/hicolor/scalable/apps', ['data/icons/vidcutter.svg']),
                ('/usr/share/pixmaps', ['data/icons/vidcutter.svg']),
                ('/usr/share/applications', ['data/desktop/vidcutter.desktop']),
                ('/usr/share/mime/packages', ['data/mime/x-vidcutter.xml'])
            ]
        return files
