#!/usr/bin/env python3
# -*- mode: python -*-

import os
import sys


block_cipher = None

a = Analysis(['..\\..\\vidcutter.py'],
             pathex=['%s\\Lib\\site-packages\\PyQt5\\Qt\\bin' % os.path.dirname(sys.executable),
             'C:\\Program Files (x86)\\Windows Kits\\10\Redist\\ucrt\\DLLs\\x86',
             '..\\..'],
             binaries=[],
             datas=[('..\\..\\bin\\ffmpeg.exe', '.\\bin')],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          name='vidcutter',
          debug=False,
          strip=False,
          upx=False,
          console=False , icon='..\\..\\images\\vidcutter.ico')
