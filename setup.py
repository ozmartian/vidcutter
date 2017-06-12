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
import shlex
import subprocess
import sys

from distutils.spawn import find_executable
from setuptools import setup
from setuptools.extension import Extension


def get_value(varname, filename='vidcutter/__init__.py'):
    with codecs.open(os.path.join(here, filename), encoding='utf-8') as initfile:
        for line in initfile.readlines():
            m = re.match('__%s__ *= *[\'](.*)[\']' % varname, line)
            if m:
                return m.group(1)


def get_description(filename='README.md'):
    with codecs.open(os.path.join(here, filename), encoding='utf-8') as f:
        file = list(f)
    desc = ''
    for item in file[11: len(file)]:
        desc += item
    return desc


def get_install_requires():
    return ['PyQt5', 'PyOpenGL'] if packager == 'pypi' else []


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

here = os.path.abspath(os.path.dirname(__file__))

packager = get_value('packager')

extensions = []
if sys.platform != 'win32':
    from Cython.Build import cythonize
    extensions = cythonize([Extension(
        'vidcutter.libs.mpv',
        ['vidcutter/libs/pympv/mpv.pyx'],
        libraries=['mpv'],
        extra_compile_args=['-g0']
    )])

result = setup(
    name='vidcutter',
    version=get_value('version'),
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='the simplest + fastest video cutter & joiner',
    long_description=get_description(),
    url='http://vidcutter.ozmartians.com',
    license='GPLv3+',

    packages=['vidcutter', 'vidcutter.libs'],

    setup_requires=['setuptools', 'Cython' if sys.platform != 'win32' else ''],

    install_requires=get_install_requires(),

    data_files=get_data_files(),

    ext_modules=extensions,

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

ROOT = os.geteuid() == 0
if not sys.platform.startswith('linux') or not os.getenv('FAKEROOTKEY') is None:
    ROOT = False

if ROOT and not result is None:
    try:
        sys.stdout.write('Updating shared mime-info database... ')
        exepath = find_executable('update-mime-database')
        if exepath is None:
            raise Exception
        subprocess.call([exepath, '/usr/share/mime/'])
    except:
        sys.stdout.write('FAILED\n')
    else:
        sys.stdout.write('DONE\n')

    try:
        exepath = find_executable('update-desktop-database')
        if exepath is None:
            raise Exception
        sys.stdout.write('Updating desktop file database... ')
        subprocess.call([exepath])
    except:
        sys.stdout.write('FAILED\n')
    else:
        sys.stdout.write('DONE\n')

    try:
        sys.stdout.write('Updating mime-type and file-type info... ')
        exepath = find_executable('xdg-icon-resource')
        if exepath is None:
            raise Exception
        args = exepath + ' ' + \
            'install --noupdate --context mimetypes --size 128 ' + \
            '/usr/share/icons/hicolor/128x128/apps/vidcutter.png ' + \
            'application-x-vidcutter'
        subprocess.call(shlex.split(args))
    except:
        sys.stdout.write('FAILED\n')
    else:
        sys.stdout.write('DONE\n')
