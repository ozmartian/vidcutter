#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

setup(
    name='vidcutter-demo',
    version='0.4.1',
    ext_modules=cythonize([
        Extension('mpv', ['mpv.c'],
                  libraries=['mpv'])
    ])
)
