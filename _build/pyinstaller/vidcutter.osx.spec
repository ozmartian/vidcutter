#!/usr/bin/env python3
# -*- mode: python -*-

import os
import sys
import PyQt5

block_cipher = None


a = Analysis(['../../vidcutter/__main__.py'],
             pathex=[
                 os.path.join(sys.modules['PyQt5'].__path__[0], 'Qt', 'bin'),
                 '../..'
             ],
             binaries=[],
             datas=[
                 ('../../vidcutter/__init__.py', '.'),
                 ('../../bin/ffmpeg', 'bin'),
                 ('../../bin/mediainfo', 'bin')
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
          upx=False,
          console=False , icon='../../data/icons/vidcutter.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=True,
               upx=False,
               name='VidCutter')
app = BUNDLE(coll,
             name='VidCutter.app',
             icon='../../data/icons/vidcutter.icns',
             bundle_identifier='com.ozmartians.vidcutter')
