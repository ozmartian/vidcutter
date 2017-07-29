#!/usr/bin/env python3
# -*- mode: python -*-

from PyQt5.QtCore import QLibraryInfo


block_cipher = None

a = Analysis(['../../vidcutter/__main__.py'],
             pathex=[
                 QLibraryInfo.location(QLibraryInfo.LibrariesPath),
                 QLibraryInfo.location(QLibraryInfo.PluginsPath),
                 '../..'
             ],
             # binaries=[
             #    ('/usr/lib/x86_64-linux-gnu/mesa/libGL.so.1.2.0', '.')
             # ],
             binaries=[
                 ('/home/ozmartian/.local/share/Steam/ubuntu12_32/steam-runtime/amd64/lib/x86_64-linux-gnu/' +
                 'libselinux.so.1', '.')
             ],
             datas=[
                 ('../../vidcutter/__init__.py', '.'),
                 ('../../vidcutter/libs/mpv.*.so', '.'),
                 ('../../bin/ffmpeg', './bin'),
                 ('../../bin/mediainfo', './bin'),
                 ('../../LICENSE', '.'),
                 ('../../README.md', '.')
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
          a.binaries,
          a.zipfiles,
          a.datas,
          name='vidcutter',
          debug=False,  
          strip=True,
          upx=True,
          console=True )
