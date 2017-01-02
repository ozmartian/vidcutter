#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import sys
import sysconfig
from codecs import open
from os import path, remove
from re import match

from setuptools import setup

here = path.abspath(path.dirname(__file__))

def get_version(filename='__init__.py'):
    with open(path.join(here, filename), encoding='utf-8') as initfile:
        for line in initfile.readlines():
            m = match('__version__ *= *[\'](.*)[\']', line)
            if m:
                return m.group(1)

def get_description(filename='README.md'):
    with open(path.join(here, filename), encoding='utf-8') as f:
        return f.read()

def get_architecture():
    bits = struct.calcsize('P') * 8
    return 'win-amd64' if bits == 64 else 'win32'

def get_package_data():
    if sys.platform == 'win32':
        if path.exists('bin/ffmpeg.zip'):
            remove('bin/ffmpeg.zip')
        arch = sys.argv[3] if sys.argv[1] == 'bdist_wheel' else sysconfig.get_platform()
        if arch == 'win32':
            shutil.copy(path.join(here, 'bin', 'x86', 'ffmpeg.zip'), path.join(here, 'bin'))
        elif arch == 'win-amd64':
            shutil.copy(path.join(here, 'bin', 'x64', 'ffmpeg.zip'), path.join(here, 'bin'))
        return ['bin/ffmpeg.zip', 'LICENSE', 'README.md']
    else:
        return ['LICENSE', 'README.md']

setup(
    name='vidcutter',
    version=get_version(),
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='FFmpeg based video cutter & joiner with a modern PyQt5 GUI',
    long_description=get_description(),
    url='http://vidcutter.ozmartians.com',
    license='GPLv3+',

    packages=['vidcutter'],

    package_dir={'vidcutter': '.'},

    setup_requires=['setuptools >= 26.1.1'],

    install_requires=['PyQt5 >= 5.5', 'qtawesome >= 0.3.3'],

    package_data={'vidcutter': get_package_data()},

    data_files=[
        ('/usr/share/pixmaps', ['data/pixmaps/vidcutter.png']),
        ('/usr/share/applications', ['data/desktop/vidcutter.desktop'])
    ],

    entry_points={'gui_scripts': ['vidcutter = vidcutter.vidcutter:main']},

    keywords='vidcutter audiovideoediting audiovideo videoeditor video videoedit pyqt Qt5 multimedia',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Communications :: File Sharing',
        'Programming Language :: Python :: 3.5'
    ]
)
