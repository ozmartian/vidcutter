#!/usr/bin/env python3
# -*- mode: python -*-

import os
import sys

import PyQt5
import qtawesome

block_cipher = None


a = Analysis(['../../vidcutter.py'],
             pathex=[
                 os.path.join(sys.modules['PyQt5'].__path__[0], 'Qt', 'bin'),
                 '../..'
             ],
             binaries=[],
             datas=[
                 ('../../__init__.py', '.'),
                 (os.path.join(sys.modules['qtawesome'].__path__[0], 'fonts', '*'), './qtawesome/fonts')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='VidCutter',
          debug=False,
          strip=True,
          upx=True,
          console=False , icon='../../images/vidcutter.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=True,
               upx=True,
               name='VidCutter')
app = BUNDLE(coll,
             name='VidCutter.app',
             icon='../../images/vidcutter.icns',
             bundle_identifier='com.ozmartians.vidcutter')
