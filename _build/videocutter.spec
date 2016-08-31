# -*- mode: python -*-

block_cipher = None

binaries = [
    ( 'C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\\DLLs\\x64', '.' )
]

data_files = [
  ('bin/', 'bin'),
  ('icons/', 'icons'),
  ('fonts/', 'fonts')
]

a = Analysis(['videocutter.py'],
             pathex=['C:\\DEV\\videocutter'],
             binaries=binaries,
             datas=data_files,
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
          name='videocutter',
          debug=False,
          strip=False,
          upx=False,
          console=False , icon='icons\\videocutter.ico')
