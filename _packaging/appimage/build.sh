#!/bin/bash

export ARCH="x86_64"
export NO_GLIBC_VERSION="1"
export VERSION="6.0.5.1"

wget https://github.com/AppImage/AppImages/raw/master/pkg2appimage
chmod +x ./pkg2appimage

./pkg2appimage ./VidCutter.yml
rm ./pkg2appimage
