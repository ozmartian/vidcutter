@echo off

rd /s /q build
rd /s /q dist
pyinstaller --clean vidcutter.win.spec
