@echo off

cd ..
nuitka --recurse-all --remove-output --windows-disable-console --windows-icon=icons\vidcutter.ico vidcutter.py
ren vidcutter.exe vidcutter.exe
