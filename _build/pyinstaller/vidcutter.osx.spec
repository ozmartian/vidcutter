#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
# noinspection PyUnresolvedReferences
import PyQt5
import sys
sys.path.insert(0, "../..")

import vidcutter

block_cipher = None

# noinspection PyUnresolvedReferences
a = Analysis(['../../vidcutter/__main__.py'],
             pathex=[
                 os.path.join(sys.modules['PyQt5'].__path__[0], 'Qt', 'bin'),
                 '../..'
             ],
             binaries=[],
             datas=[
                 ('../../vidcutter/__init__.py', '.'),
                 ('../../CHANGELOG', '.'),
                 ('../../LICENSE', '.'),
                 ('../../README.md', '.'),
                 ('../../bin/*', 'bin')
             ],
             hiddenimports=['PyQt5.sip'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['numpy'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

# noinspection PyUnresolvedReferences
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# noinspection PyUnresolvedReferences
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=vidcutter.__appname__,
          debug=False,
          strip=True,
          upx=False,
          console=False,
          icon='../../data/icons/vidcutter.icns')

# noinspection PyUnresolvedReferences
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=True,
               upx=False,
               name=vidcutter.__appname__)

# noinspection PyUnresolvedReferences
app = BUNDLE(coll,
             name='{}.app'.format(vidcutter.__appname__),
             icon='../../data/icons/vidcutter.icns',
             bundle_identifier=vidcutter.__desktopid__,
             info_plist={
                'CFBundleShortVersionString': vidcutter.__version__,
                'NSHighResolutionCapable': 'True'
             })
