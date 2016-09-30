# -*- mode: python -*-

block_cipher = None


a = Analysis(['..\\vidcutter.py'],
             pathex=['C:\\Python35\\Lib\\site-packages\\PyQt5\\Qt\\bin', 'C:\\DEV\\vidcutter'],
             binaries=[],
             datas=[('..\\bin\\ffmpeg.exe', '.\\bin\\')],
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
          console=False , icon='..\\images\\vidcutter.ico')
