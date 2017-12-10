#!/bin/bash

export NO_GLIBC_VERSION="1"

wget https://github.com/AppImage/AppImages/raw/master/pkg2appimage
chmod +x ./pkg2appimage

./pkg2appimage VidCutter.yml
mv ./out/VidCutter--x86_64.AppImage ./out/VidCutter-${BUILD_VERSION}-x64.AppImage
rm ./pkg2appimage
