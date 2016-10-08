#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='VidCutter',
    version='1.5',
    packages=find_packages('vidcutter'),
    url='http://vidcutter.ozmartians.com',
    license='GPLv3+',
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='Simple FFmpeg based media cutter + joiner',
    long_description=read('README.md'),
    # install_requires=['pyqt5']
)
