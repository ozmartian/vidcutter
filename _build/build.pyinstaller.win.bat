@echo off

rm -rf dist build
pyinstaller -F -w --clean -n vidcutter -i ..\icons\vidcutter.ico vidcutter.spec
