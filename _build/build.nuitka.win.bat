@echo off

cd ..
nuitka --recurse-all --remove-output --windows-disable-console --windows-icon=icons\videocutter.ico videocutter.py
ren videocutter.exe vidcutter.exe
