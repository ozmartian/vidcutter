@echo off

rm -rf dist build
pyinstaller -F -w --clean -n vidcutter -i ..\images\vidcutter.ico vidcutter.spec
