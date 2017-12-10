#!/bin/bash

wget https://github.com/AppImage/AppImages/raw/master/pkg2appimage
chmod +x ./pkg2appimage

export NO_GLIBC_VERSION="1"
./pkg2appimage VidCutter.yml
rm ./pkg2appimage

export BUILD_VERSION="$(python3 ../../_build/pyinstaller/version.py)"
[ -r out/VidCutter-*.AppImage ] && mv out/VidCutter-*-x86_64.AppImage out/VidCutter-${BUILD_VERSION}-x64.AppImage
