@echo off

for /f "delims=" %%a in ('python ..\pyinstaller\version.py') do @set VERSION=%%a

"C:\Program Files (x86)\Inno Setup 5\iscc.exe" installer.iss

verpatch Output\VidCutter-%VERSION%-setup-x64.exe /va %VERSION% /pv %VERSION% /s desc "VidCutter" /s name "VidCutter" /s copyright "© 2017 Pete Alexandrou" /s product "VidCutter x64 Installer" /s company "ozmartians.com"