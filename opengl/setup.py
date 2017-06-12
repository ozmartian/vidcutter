#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from setuptools import setup
from setuptools.extension import Extension

extensions = []

if sys.platform != 'win32':
    from Cython.Build import cythonize
    extensions = cythonize([Extension(
        'vidcutter_demo.mpv',
        ['vidcutter_demo/pympv/mpv.pyx'],
        libraries=['mpv'],
        extra_compile_args=['-g0']
    )])


setup(
    name='vidcutter_demo',
    version='1.0.0',
    description='Testing Cython install options',
    long_description='i am a long description',
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    url='http://vidcutter.ozmartians.com',
    license='GPLv3+',
    packages=['vidcutter_demo'],
    setup_requires=['setuptools', 'Cython' if sys.platform != 'win32' else ''],
    entry_points={'gui_scripts': ['vidcutter_demo = vidcutter_demo.__main__:main']},
    ext_modules=extensions,
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
