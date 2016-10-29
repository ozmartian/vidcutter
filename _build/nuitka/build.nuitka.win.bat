@echo off

cd ../..
nuitka --recurse-all --remove-output --windows-disable-console --windows-icon=images\vidcutter.ico vidcutter.py
