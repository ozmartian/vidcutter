#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    for item in file[6: len(file)]:
        desc += item
    return desc


def get_install_requires():
    if packager == 'pypi':
        return ['PyQt5 >= 5.5']
    else:
        return []


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
            ('/usr/share/applications', ['data/desktop/vidcutter.desktop'])
        ]
    files.append(('.', ['README.md', 'LICENSE']))
    return files


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

    package_dir={'vidcutter': 'vidcutter'},

    setup_requires=['setuptools'],

    install_requires=get_install_requires(),

    package_data={'vidcutter': [
        'data/desktop/*.*',
        'data/icons/*.*'
    ]},

    data_files=get_data_files(),

    entry_points={'gui_scripts': ['vidcutter = vidcutter.__main__:main']},

    keywords='vidcutter audiovideoediting audiovideo videoeditor video videoedit pyqt Qt5 multimedia',

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
