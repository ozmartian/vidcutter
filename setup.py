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
# *** IMPORTANT IF YOU ARE INSTALLING VIA PyPi (Python Pip) ***
#
# no longer enforcing dependencies via setuptools
# a notifcation msg is now displayed detailing requirements so users from PyPi,
# Conda or obscure distros can get them installed however they like.
# Distro targetted packages will always be the recommended approach
#

import os

from setuptools import setup
from setuptools.extension import Extension

from helpers import SetupHelpers
import vidcutter

setup_requires = ['setuptools']

# Cython override; default to building extension module from pre-Cythonized .c file
USE_CYTHON = True if not os.path.isfile('vidcutter/libs/pympv/mpv.c') else False

extensions = [Extension(name='vidcutter.libs.mpv',
                        sources=['vidcutter/libs/pympv/mpv.{}'.format('c' if not USE_CYTHON else 'pyx')],
                        include_dirs=['vidcutter/libs/pympv/mpv'],
                        libraries=['mpv'],
                        library_dirs=SetupHelpers.get_library_dirs(),
                        extra_compile_args=['-g0' if os.name == 'posix' else ''])]

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
        description='the simplest + fastest media cutter and joiner',
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
