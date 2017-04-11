#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from codecs import open
from os import path
from re import match, sub

with open(path.join(path.abspath(path.dirname(__file__)),
                    '../../vidcutter/__init__.py'), encoding='utf-8') as initfile:
    for line in initfile.readlines():
        m = match('__version__ *= *[\'](.*)[\']', line)
        if m:
            print(sub('rc(.*)$', '', m.group(1)))
