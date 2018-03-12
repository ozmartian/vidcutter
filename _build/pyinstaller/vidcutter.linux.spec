#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import vidcutter

block_cipher = None

# noinspection PyUnresolvedReferences
a = Analysis(['../../vidcutter/__main__.py'],
             pathex=[],
             binaries=[],
             datas=[
                 ('../../vidcutter/__init__.py', '.'),
                 ('../../bin/*', 'bin')
             ],
             hiddenimports=[],
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
          upx=True,
          console=True)

# noinspection PyUnresolvedReferences
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=True,
               upx=True,
               name=vidcutter.__appname__)
