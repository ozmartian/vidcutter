#!/bin/bash

export NO_GLIBC_VERSION="1"

wget https://github.com/AppImage/AppImages/raw/master/pkg2appimage
chmod +x ./pkg2appimage

./pkg2appimage ./VidCutter.yml
rm ./pkg2appimage
