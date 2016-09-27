#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='VidCutter',
    version='1.0.5',
    packages=find_packages(),
    url='http://vidcutter.ozmartians.com',
    license='GPLv3+',
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='Simple video cutter & joiner based on FFmpeg',
    long_description=read('README.md'),
    install_requires=['PyQt5']
)
