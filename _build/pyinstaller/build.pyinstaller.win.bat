@echo off

REM ......................setup variables......................

if [%1]==[] (
    SET ARCH=64
) else (
    SET ARCH=%1
)

if ["%ARCH%"]==["64"] (
    SET BINARCH=x64
    SET FFMPEG_URL=https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-latest-win64-static.7z
    SET FFMPEG=ffmpeg-latest-win64-static.7z
    SET MEDIAINFO_URL=https://mediaarea.net/download/binary/mediainfo/0.7.97/MediaInfo_CLI_0.7.97_Windows_x64.zip
    SET MEDIAINFO=MediaInfo_CLI_0.7.97_Windows_x64.zip
)
if ["%ARCH%"]==["32"] (
    SET BINARCH=x86
    SET FFMPEG_URL=https://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-latest-win32-static.7z
    SET FFMPEG=ffmpeg-latest-win32-static.7z
    SET MEDIAINFO_URL=https://mediaarea.net/download/binary/mediainfo/0.7.97/MediaInfo_CLI_0.7.97_Windows_i386.zip
    SET MEDIAINFO=MediaInfo_CLI_0.7.97_Windows_i386.zip
)

REM ......................get latest version number......................

for /f "delims=" %%a in ('C:\Python36-x64\python.exe version.py') do @set APPVER=%%a

REM ......................cleanup previous build scraps......................

rd /s /q build
rd /s /q dist
if not exist "..\..\bin\" mkdir ..\..\bin\
del /q ..\..\bin\*.*

REM ......................download latest FFmpeg static binary......................

if not exist ".\temp\" mkdir temp
if not exist "temp\ffmpeg-latest-win%ARCH%-static.7z" ( curl -L -fsS -o temp\%FFMPEG% "%FFMPEG_URL%" )
if not exist "temp\%MEDIAINFO%" ( curl -L -fsS -o temp\%MEDIAINFO% "%MEDIAINFO_URL%" )

REM ......................extract ffmpeg.exe to its expected location......................

cd temp\
7z e ffmpeg-latest-win%ARCH%-static.7z ffmpeg-latest-win%ARCH%-static/bin/ffmpeg.exe
unzip %MEDIAINFO% MediaInfo.exe
if not exist "..\..\..\bin\" mkdir "..\..\..\bin\"
move ffmpeg.exe ..\..\..\bin\
move MediaInfo.exe ..\..\..\bin\
cd ..

REM ......................run pyinstaller......................

C:\Python36-x64\scripts\pyinstaller.exe --clean vidcutter.win%ARCH%.spec

REM ......................add metadata to built Windows binary......................

.\verpatch.exe dist\vidcutter.exe /va %APPVER%.0 /pv %APPVER%.0 /s desc "VidCutter" /s name "VidCutter" /s copyright "(c) 2017 Pete Alexandrou" /s product "VidCutter %BINARCH%" /s company "ozmartians.com"

REM ......................call Inno Setup installer build script......................

cd ..\InnoSetup
"C:\Program Files (x86)\Inno Setup 5\iscc.exe" installer_%BINARCH%.iss

cd ..\pyinstaller
