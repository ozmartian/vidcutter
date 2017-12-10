#!/bin/bash

wget https://github.com/AppImage/AppImages/raw/master/pkg2appimage
chmod +x ./pkg2appimage

export NO_GLIBC_VERSION="1"
export VERSION="${BUILD_VERSION}"

./pkg2appimage VidCutter.yml
rm ./pkg2appimage
