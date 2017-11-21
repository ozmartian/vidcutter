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
#
# *** IMPORTANT: READ IF INSTALLING VIA PyPi (Pip) ***
#
# dependencies are no lonfer enforced via setuptools scripts; its too limiting and
# Python only AND conflicts with package handling dependencies when dealing with all
# flavours and distros in Linux. If you're on Windows or macOS then you should NOT
# be reading this and simply grab the latest pre-built release installer from our
# GitHub releases page (https://github.com/ozmartian/vidcutter/releases/latest)
# if you have sourced this via PyPi (Pip) or Conda then see SetupHelpers.pip_notes()
# in helpers.py for details regarding dependencies and other non-Pythonic requirements
# Linux distro packages or our pre-built AppImage binary is the author's recommendation
# unless you're either a developer or know you're way around all (if not, why are
# you even reading this right now?! :-)
#
#######################################################################

import os
import sys

from setuptools import setup
from setuptools.extension import Extension

from helpers import SetupHelpers
import vidcutter

setup_requires = ['setuptools']

# Cython override; default to building extension module from pre-Cythonized .c file
USE_CYTHON = True if not os.path.isfile(os.path.join('vidcutter', 'libs', 'pympv', 'mpv.c')) else False
ext = '.pyx' if USE_CYTHON else '.c'
extensions = [Extension(
    'vidcutter.libs.mpv',
    ['vidcutter/libs/pympv/mpv{0}'.format(ext)],
    include_dirs=['vidcutter/libs/pympv/mpv'],
    libraries=['mpv'],
    library_dirs=SetupHelpers.get_library_dirs(),
    extra_compile_args=['-g0' if sys.platform != 'win32' else '']
)]
if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)
    setup_requires.append('Cython')

try:
    # begin setuptools installer
    result = setup(
        name=vidcutter.__appname__.lower(),
        version=vidcutter.__version__,
        author=vidcutter.__author__,
        author_email=vidcutter.__email__,
        description='the simplest + fastest video cutter and joiner',
        long_description=SetupHelpers.get_description(),
        url=vidcutter.__website__,
        license='GPLv3+',
        packages=['vidcutter', 'vidcutter.libs'],
        setup_requires=setup_requires,
        install_requires=[],
        data_files=SetupHelpers.get_data_files(),
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
except BaseException:
    if vidcutter.__ispypi__:
        SetupHelpers.pip_notes()
    raise
