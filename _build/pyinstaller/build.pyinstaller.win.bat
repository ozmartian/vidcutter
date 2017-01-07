@echo off

if [%1]==[] (
    SET ARCH=64
) else (
    SET ARCH=%1
)

if ["%ARCH%"]==["64"] (
    SET BINARCH=x64
)
if ["%ARCH%"]==["32"] (
    SET BINARCH=x86
)

rd /s /q build
rd /s /q dist
del ..\..\bin\ffmpeg.exe

unzip ..\..\bin\%BINARCH%\ffmpeg.zip -d ..\..\bin\

pyinstaller --clean vidcutter.win%ARCH%.spec

verpatch.exe dist\vidcutter.exe /va 2.0.1.0 /pv 2.0.1.0 /s desc "VidCutter" /s name "VidCutter" /s copyright "2017 Pete Alexandrou" /s product "VidCutter %BINARCH%"