@echo off

if [%1]==[] (
    SET ARCH=64
) else (
    SET ARCH=%1
)


rd /s /q build
rd /s /q dist
pyinstaller --clean vidcutter.win%ARCH%.spec
