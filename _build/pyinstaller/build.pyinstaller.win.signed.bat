@echo off

setlocal

REM ......................setup variables......................
if [%1]==[] (
    goto :usage
) else (
    SET ARCH=%1
)

if [%2]==[] (
    goto :usage
) else (
    SET PASS=%2
)

if ["%ARCH%"]==["64"] (
    SET BINARCH=x64
    SET PYPATH=C:\Python36-x64
    REM SET FFMPEG_URL=https://ffmpeg.zeranoe.com/builds/win64/shared/ffmpeg-latest-win64-shared.zip
    SET FFMPEG_URL=https://ffmpeg.zeranoe.com/builds/win64/shared/ffmpeg-4.0.2-win64-shared.zip
    REM SET FFMPEG=ffmpeg-latest-win64-shared.zip
    SET FFMPEG=ffmpeg-4.0.2-win64-shared.zip
    SET MEDIAINFO_URL=https://mediaarea.net/download/binary/mediainfo/18.05/MediaInfo_CLI_18.05_Windows_x64.zip
    SET MEDIAINFO=MediaInfo_CLI_18.05_Windows_x64.zip
)
if ["%ARCH%"]==["32"] (
    SET BINARCH=x86
    SET PYPATH=C:\Python36
    REM SET FFMPEG_URL=https://ffmpeg.zeranoe.com/builds/win32/shared/ffmpeg-latest-win32-shared.zip
    SET FFMPEG_URL=https://ffmpeg.zeranoe.com/builds/win32/shared/ffmpeg-4.0.2-win32-shared.zip
    REM SET FFMPEG=ffmpeg-latest-win32-shared.zip
    SET FFMPEG=ffmpeg-4.0.2-win32-shared.zip
    SET MEDIAINFO_URL=https://mediaarea.net/download/binary/mediainfo/18.05/MediaInfo_CLI_18.05_Windows_i386.zip
    SET MEDIAINFO=MediaInfo_CLI_18.05_Windows_i386.zip
)

REM ......................get latest version number......................
for /f "delims=" %%a in ('%PYPATH%\python.exe version.py') do @set APPVER=%%a

REM ......................cleanup previous build scraps......................
rd /s /q build
rd /s /q dist
if not exist "..\..\bin\" ( mkdir ..\..\bin\ ) else ( del /q ..\..\bin\*.* )

REM ......................download latest FFmpeg & MediaInfo shared binary + libs ......................
if not exist ".\temp\" mkdir temp
if not exist "temp\%FFMPEG%" ( call curl -k -L -# -o temp\%FFMPEG% "%FFMPEG_URL%" )
if not exist "temp\%MEDIAINFO%" ( call curl -k -L -# -o temp\%MEDIAINFO% "%MEDIAINFO_URL%" )

REM ......................extract files & move them to top-level binary folder ......................
cd temp\
7z x "%FFMPEG%" ffmpeg-4.0.2-win%ARCH%-shared\bin
del /q ffmpeg-4.0.2-win%ARCH%-shared\bin\ffplay.exe
unzip "%MEDIAINFO%" MediaInfo.exe
move ffmpeg-4.0.2-win%ARCH%-shared\bin\*.* ..\..\..\bin\
move MediaInfo.exe ..\..\..\bin\
cd ..

REM ......................run pyinstaller......................
"%PYPATH%\scripts\pyinstaller.exe" --clean vidcutter.win%ARCH%.spec

if exist "dist\vidcutter.exe" (
    REM ......................add metadata to built Windows binary......................
    .\verpatch.exe dist\vidcutter.exe /va %APPVER%.0 /pv %APPVER%.0 /s desc "VidCutter" /s name "VidCutter" /s copyright "(c) 2020 Pete Alexandrou" /s product "VidCutter %BINARCH%" /s company "ozmartians.com"

    REM ................sign frozen EXE with self-signed certificate..........
    SignTool.exe sign /f "..\certs\code-sign.pfx" /t http://timestamp.comodoca.com/authenticode /p %PASS% dist\vidcutter.exe

    REM ......................call Inno Setup installer build script......................
    cd ..\InnoSetup
    call "C:\Program Files (x86)\Inno Setup 5\iscc.exe" installer_%BINARCH%.iss

    REM ................sign final redistributable EXE with self-signed certificate..........
    SignTool.exe sign /f "..\certs\code-sign.pfx" /t http://timestamp.comodoca.com/authenticode /p %PASS% output\VidCutter-%APPVER%-setup-win%ARCH%.exe

    cd ..\pyinstaller
)

goto :eof

:usage
    echo.
    echo Usage:
    echo. 
    echo   build.pyinstaller.win.signed arch [pfxpass]
    echo. 
    goto :eof

:eof
    endlocal
    exit /b
