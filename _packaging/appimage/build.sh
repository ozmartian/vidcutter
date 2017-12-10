#!/bin/bash

export NO_GLIBC_VERSION="1"

wget https://github.com/AppImage/AppImages/raw/master/pkg2appimage
chmod +x ./pkg2appimage

if [ -z ${BUILD_VERSION} ]; then
	echo "$(python ../../_build/pyinstaller/version.py)" > VERSION
else
    echo "${BUILD_VERSION}" > VERSION
fi

./pkg2appimage VidCutter.yml
rm ./pkg2appimage
rm ./VERSION
