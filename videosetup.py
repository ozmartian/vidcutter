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


    @staticmethod
    def yesno(question: str) -> bool:
        _yesno = {'Y': True, 'y': True, 'n': False, 'N': False, 'yes': True, 'no': False}
        choice = input(question).lower().strip

    @staticmethod
    def install_notes():
        msg = '''
*****************************************************************************

    VidCutter depends on the following in order to run on a typical
    Linux installation. The corresponding 
    
        - Python 3 w/ development headers
        
            * Ubuntu/Debian/Mint/etc:   python3-dev
            * Fedora:                   python3-devel
            * openSUSE:                 python3-devel
            * Arch Linux:               python
    
        - libmpv & mpv development headers

            * Ubuntu/Debian/Mint/etc:   libmpv1 limpv-dev
            * Fedora:                   mpv-libs mpv-libs-devel
            * openSUSE:                 libmpv1 mpv-devel
            * Arch Linux:               mpv

        - PyQt5 w/ OpenGL module
         
            * Ubuntu/Debian/Mint/etc:   python3-pyqt5 python3-pyqt5.qtopengl
            * Fedora:                   python3-qt5
            * openSUSE:                 python3-qt5
            * Arch Linux:               python-pyqt5
            
        - PyOpenGL python module
        
            * Ubuntu/Debian/Mint/etc:   python3-opengl
            * Fedora:                   python3-pyopengl
            * openSUSE:                 python3-opengl
            * Arch Linux                python-opengl
        
        - FFmpeg

            * Ubuntu/Debian/Mint/etc:   ffmpeg
            * Fedora:                   ffmpeg
            * openSUSE:                 ffmpeg
            * Arch Linux                ffmpeg
            
        - MediaInfo
        
            * Ubuntu/Debian/Mint/etc:   mediainfo
            * Fedora:                   mediainfo
            * openSUSE:                 mediainfo
            * Arch Linux:               mediainfo
            
    You need to build a Python extension module before you can run the
    app directly from the source code. This is all handled automatically
    by the package installers by the setuptools install script. If you
    wish to simply run the app direct from source without having to 
    install it (i.e. python3 setup.py install) you can do so by building
    the extension module with the following setuptools command, run from
    the root source folder:
    
        $ python3 setup.py build_ext -i
        
    Make sure you build the extension module AFTER installing the
    dependencies covered above, in particular libmpv and the mpv + python3
    dev headers are all needed for it to compile successfully. Upon success
    you should have a new file under vidcutter/libs named something like:
    
        mpv.cpython-<python version + platform>.so (Linux/macOS)
        mpv.cp-<python version + platform>.pyd     (Windows)
        
    Windows users can also build for themselves as long as you run 
    the Python command from a Visual Studio 2015/2017 Native x64/x86
    Developer Command Prompt terminal but you will need mvp libs for
    Windows plus other things, trust me when I say you're best off simply
    downloading the Windows setup from the releases page.
    
        https://github.com/ozmartian/vidcutter/releases/latest
    
*****************************************************************************
'''
        input('Would you like to see the install notes (recommended)? [y/n]r')
        return msg
