# Maintainer: Pete Alexandrou (ozmartian) <pete@ozmartians.com>
pkgname=vidcutter-git
pkgver=2.0.0.r0.gde179c3
pkgrel=1
pkgdesc="FFmpeg based video cutter & joiner with a modern PyQt5 GUI"
arch=('any')
license=('GPL3')
url="http://vidcutter.ozmartians.com"
source=('vidcutter-git::git+https://github.com/ozmartian/vidcutter.git')
depends=('python-pyqt5' 'qt5-multimedia' 'ffmpeg' 'python-qtawesome-git')
makedepends=('git' 'python-setuptools')
provides=()
conflicts=('vidcutter')
md5sums=('SKIP')

pkgver() {
    cd "${pkgname}"
    git describe --long | sed 's/\([^-]*-g\)/r\1/;s/-/./g'
}

build() {
    cd "${srcdir}/${pkgname}"
    python setup.py build
}

package() {
    cd "${srcdir}/${pkgname}"
    python3 setup.py install --root="${pkgdir}" --optimize=1 --skip-build
    install -Dm644 "_build/vidcutter.desktop" "${pkgdir}/usr/share/applications/vidcutter.desktop"
    install -Dm644 "images/vidcutter.png" "${pkgdir}/usr/share/pixmaps/vidcutter.png"
}
