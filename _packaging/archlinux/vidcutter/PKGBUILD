# Maintainer: Pete Alexandrou (ozmartian) <pete@ozmartians.com>
pkgname=vidcutter
pkgver=2.0.0
pkgrel=1
pkgdesc="FFmpeg based video cutter & joiner with a modern PyQt5 GUI"
arch=('any')
license=('GPL3')
url="http://vidcutter.ozmartians.com"
source=(https://github.com/ozmartian/${pkgname}/archive/${pkgver}.tar.gz)
depends=('python-pyqt5' 'qt5-multimedia' 'ffmpeg' 'python-qtawesome-git')
makedepends=('git' 'python-setuptools')
provides=()
conflicts=('vidcutter')
md5sums=('SKIP')

build() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    python setup.py build
}

package() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    python3 setup.py install --root="${pkgdir}" --optimize=1 --skip-build
    install -Dm644 "_build/${pkgname}.desktop" "${pkgdir}/usr/share/applications/${pkgname}.desktop"
    install -Dm644 "images/${pkgname}.png" "${pkgdir}/usr/share/pixmaps/${pkgname}.png"
}
