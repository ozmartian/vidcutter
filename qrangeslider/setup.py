#!/usr/bin/env python
# 
# Copyright (C) 2011-2014 Ryan Galloway (ryan@rsgalloway.com)
#
# This module is part of Shotman and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php

from distutils.core import setup
from qrangeslider import __version__
setup(name='qrangeslider',
      version=__version__,
      description='The QRangeSlider class implements a horizontal PyQt range slider widget.',
      author='Ryan Galloway',
      author_email='ryan@rsgalloway.com',
      url='http://github.com/rsgalloway/qrangeslider',
      py_modules=['qrangeslider']
      )
