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
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

import sys
from codecs import open
from os import path
from re import match

from setuptools import setup


def get_value(varname, filename='vidcutter/__init__.py'):
    with open(path.join(here, filename), encoding='utf-8') as initfile:
        for line in initfile.readlines():
            m = match('__%s__ *= *[\'](.*)[\']' % varname, line)
            if m:
                return m.group(1)


def get_description(filename='README.md'):
    with open(path.join(here, filename), encoding='utf-8') as f:
        file = list(f)
    desc = ''
    for item in file[11: len(file)]:
        desc += item
    return desc


def get_install_requires():
    deps = []
    if packager == 'pypi':
        deps.append('PyQt5')
    return deps


def get_data_files():
    files = []
    if sys.platform.startswith('linux'):
        files = [
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
            ('/usr/share/applications', ['data/desktop/vidcutter.desktop'])
        ]
    return files

here = path.abspath(path.dirname(__file__))

packager = get_value('packager')

setup(
    name='vidcutter',
    version=get_value('version'),
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='the simple & fast video cutter & joiner with the help of mpv + FFmpeg',
    long_description=get_description(),
    url='http://vidcutter.ozmartians.com',
    license='GPLv3+',

    packages=['vidcutter'],

    setup_requires=['setuptools'],

    install_requires=get_install_requires(),

    data_files=get_data_files(),

    entry_points={'gui_scripts': ['vidcutter = vidcutter.__main__:main']},

    keywords='vidcutter ffmpeg audiovideo mpv libmpv videoeditor video videoedit pyqt Qt5 multimedia',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Topic :: Multimedia :: Video :: Non-Linear Editor',
        'Programming Language :: Python :: 3 :: Only'
    ]
)
