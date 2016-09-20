#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, setuptools

setup(
    name='VidCutter',
    version='1.0.1',
    url='http://vidcutter.ozmartians.com',
    license='GPL2',
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='All-in-one video cutter and joiner when you just want to get the job done simply',
    packages=setuptools.find_packages(),
    install_requires=['pyqt5>=5.6']
)
