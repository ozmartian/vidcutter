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

# *** IMPORTANT IF YOU ARE INSTALLING VIA PyPi (Python Pip) ***
#
# no longer enforcing dependencies via setuptools
# a notifcation msg is now displayed detailing requirements so users from PyPi,
# Conda or obscure distros can get them installed however they like.
# Distro targetted packages will always be the recommended approach


import os
import shlex
import subprocess
import sys
from distutils.spawn import find_executable

from setuptools import setup
from setuptools.extension import Extension

from helpers import SetupHelpers

setup_requires = ['setuptools']

# Cython override; default to building extension module from pre-Cythonized .c file
USE_CYTHON = False
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
        name='vidcutter',
        version=SetupHelpers.get_value('version'),
        author='Pete Alexandrou',
        author_email='pete@ozmartians.com',
        description='the simplest + fastest video cutter & joiner',
        long_description=SetupHelpers.get_description(),
        url='http://vidcutter.ozmartians.com',
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
except Exception as e:
    if SetupHelpers.get_value('packager') == 'pypi':
        SetupHelpers.pip_notes()
    raise e

# helper functions/procedures for PyPi on Linux installations which is frowned upon
# may get rid of this so users stick with distro packaging
if not sys.platform.startswith('linux') or not os.getenv('FAKEROOTKEY') is None:
    ROOT = False
else:
    ROOT = os.geteuid() == 0

if ROOT and result is not None:
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
        args = '{0} install --noupdate --context mimetypes --size 128 '.format(exepath) + \
               '/usr/share/icons/hicolor/128x128/apps/vidcutter.png application-x-vidcutter'
        subprocess.call(shlex.split(args))
    except:
        sys.stdout.write('FAILED\n')
    else:
        sys.stdout.write('DONE\n')
