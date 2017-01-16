#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import sys
import sysconfig
from codecs import open
from os import path, remove
from re import match

from setuptools import setup


def get_value(varname, filename='__init__.py'):
    with open(path.join(here, filename), encoding='utf-8') as initfile:
        for line in initfile.readlines():
            m = match('__%s__ *= *[\'](.*)[\']' % varname, line)
            if m:
                return m.group(1)


def get_description(filename='README.md'):
    with open(path.join(here, filename), encoding='utf-8') as f:
        file = list(f)
    desc = ''
    for item in file[6: len(file)]:
        desc += item
    return desc


def get_architecture():
    bits = struct.calcsize('P') * 8
    return 'win-amd64' if bits == 64 else 'win32'


def get_install_requires():
    if packager == 'pypi':
        return ['PyQt5 >= 5.5']
    else:
        return []


def get_data_files():
    if sys.platform.startswith('linux'):
        return [
            ('/usr/share/pixmaps', ['data/icons/vidcutter.png']),
            ('/usr/share/applications', ['data/desktop/vidcutter.desktop'])
        ]
    else:
        return []


here = path.abspath(path.dirname(__file__))

packager = get_value('packager')

setup(
    name='vidcutter',
    version=get_value('version'),
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='FFmpeg based video cutter & joiner with a modern PyQt5 GUI',
    long_description=get_description(),
    url='http://vidcutter.ozmartians.com',
    license='GPLv3+',

    packages=['vidcutter'],

    package_dir={'vidcutter': '.'},

    setup_requires=['setuptools'],

    install_requires=get_install_requires(),

    package_data={'vidcutter': ['LICENSE', 'README.md']},

    data_files=get_data_files(),

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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ]
)
