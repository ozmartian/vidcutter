#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
#
# copyright © 2018 Pete Alexandrou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#######################################################################

import locale
import logging
import os
import sys

if sys.platform.startswith('linux'):
    # noinspection PyBroadException
    try:
        import vidcutter.libs.distro as distro
        if distro.id().lower() in {'ubuntu', 'fedora'}:
            # noinspection PyUnresolvedReferences
            from OpenGL import GL
    except BaseException:
        pass

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QEvent, QTimer
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PyQt5.QtOpenGL import QGLContext
from PyQt5.QtWidgets import QOpenGLWidget, qApp

# noinspection PyUnresolvedReferences
import vidcutter.libs.mpv as mpv


def MPGetNativeDisplay(name):
    # if name == 'wl' and qApp.platformName().lower().startswith('wayland'):
    #     native = qApp.platformNativeInterface()
    #     return native.nativeResourceForWindow('display', None)
    name = name.decode()
    if name == 'opengl-cb-window-pos' and qApp.focusWindow() is not None:
        class opengl_cb_window_pos:
            x = qApp.focusWindow().x()
            y = qApp.focusWindow().y()
            width = qApp.focusWindow().width()
            height = qApp.focusWindow().height()
        return id(opengl_cb_window_pos())
    try:
        from PyQt5.QtX11Extras import QX11Info
        if QX11Info.isPlatformX11():
            return id(QX11Info.display())
    except ImportError:
        return 0
    return 0


def get_proc_address(name):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return 0
    name = name.decode()
    res = glctx.getProcAddress(name)
    if name == 'glMPGetNativeDisplay' and res is None:
        return MPGetNativeDisplay
    try:
        if sys.platform == 'win32' and res is None:
            from PyQt5.QtWidgets import QOpenGLContext
            from win32api import GetProcAddress
            handle = QOpenGLContext.openGLModuleHandle()
            if handle is not None:
                res = GetProcAddress(handle, name)
    except ImportError:
        return 0
    return res.__int__()


class mpvWidget(QOpenGLWidget):
    positionChanged = pyqtSignal(float, int)
    durationChanged = pyqtSignal(float, int)
    initialized = pyqtSignal(str)

    def __init__(self, parent=None, file=None, **mpv_opts):
        super(mpvWidget, self).__init__(parent)
        self.parent = parent
        self.filename = file
        self.mpvError = mpv.MPVError
        self.originalParent = None
        self.logger = logging.getLogger(__name__)
        locale.setlocale(locale.LC_NUMERIC, 'C')

        self.mpv = mpv.Context()

        self.setLogLevel('terminal-default')
        self.mpv.set_option('msg-level', self.msglevel)
        self.mpv.set_option('config', False)

        def _istr(o):
            return ('yes' if o else 'no') if type(o) is bool else str(o)

        # do not break on non-existant properties/options
        for opt, val in mpv_opts.items():
            try:
                self.mpv.set_option(opt.replace('_', '-'), _istr(val))
            except mpv.MPVError:
                self.logger.warning('error setting MPV option "%s" to value "%s"' % (opt, val))
                pass

        self.mpv.initialize()

        self.opengl = self.mpv.opengl_cb_api()
        self.opengl.set_update_callback(self.updateHandler)

        if sys.platform == 'win32':
            try:
                self.mpv.set_option('gpu-context', 'angle')
            except mpv.MPVError:
                self.mpv.set_option('opengl-backend', 'angle')

        self.frameSwapped.connect(self.swapped, Qt.DirectConnection)

        self.mpv.observe_property('time-pos')
        self.mpv.observe_property('duration')
        self.mpv.observe_property('eof-reached')
        self.mpv.set_wakeup_callback(self.eventHandler)

        if file is not None:
            self.initialized.connect(self.play)

    @property
    def msglevel(self):
        if os.getenv('DEBUG', False) or getattr(self.parent, 'verboseLogs', False):
            return 'all=v'
        else:
            return 'all=error'

    def setLogLevel(self, loglevel):
        self.mpv.set_log_level(loglevel)

    def shutdown(self):
        self.makeCurrent()
        if self.opengl:
            self.opengl.set_update_callback(None)
        self.opengl.uninit_gl()
        self.mpv.command('quit')
        self.mpv = None
        self.deleteLater()

    def initializeGL(self):
        if self.opengl:
            callback = 'GL_MP_MPGetNativeDisplay'
            if os.name != 'posix' or sys.platform == 'darwin' \
               or qApp.platformName().lower().startswith('wayland'):
                callback = None
            self.opengl.init_gl(callback, get_proc_address)
            if self.filename is not None:
                self.initialized.emit(self.filename)

    def paintGL(self):
        if self.opengl:
            self.opengl.draw(self.defaultFramebufferObject(), self.width(), -self.height())

    @pyqtSlot()
    def swapped(self):
        if self.opengl:
            self.opengl.report_flip(0)

    def updateHandler(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.swapped()
            self.doneCurrent()
        else:
            self.update()

    def eventHandler(self):
        while self.mpv:
            try:
                event = self.mpv.wait_event(.01)
                if event.id in {mpv.Events.none, mpv.Events.shutdown}:
                    break
                elif event.id == mpv.Events.log_message:
                    event_log = event.data
                    log_msg = '[%s] %s' % (event_log.prefix, event_log.text.strip())
                    if event_log.level in (mpv.LogLevels.fatal, mpv.LogLevels.error):
                        self.logger.critical(log_msg)
                        if event_log.level == mpv.LogLevels.fatal or 'file format' in event_log.text:
                            self.parent.errorOccurred.emit(log_msg)
                            self.parent.initMediaControls(False)
                    else:
                        self.logger.info(log_msg)
                elif event.id == mpv.Events.property_change:
                    event_prop = event.data
                    if event_prop.name == 'eof-reached' and event_prop.data:
                        self.parent.setPlayButton(False)
                        self.parent.setPosition(0)
                    elif event_prop.name == 'time-pos':
                        # if os.getenv('DEBUG', False) or getattr(self.parent, 'verboseLogs', False):
                        #     self.logger.info('time-pos property event')
                        self.positionChanged.emit(event_prop.data, self.mpv.get_property('estimated-frame-number'))
                    elif event_prop.name == 'duration':
                        # if os.getenv('DEBUG', False) or getattr(self.parent, 'verboseLogs', False):
                        #     self.logger.info('duration property event')
                        self.durationChanged.emit(event_prop.data, self.mpv.get_property('estimated-frame-count'))
            except mpv.MPVError as e:
                if e.code != -10:
                    raise e

    def showText(self, msg: str, duration: int=5, level: int=0):
        self.mpv.command('show-text', msg, duration * 1000, level)

    @pyqtSlot(str)
    def play(self, filepath) -> None:
        if os.path.isfile(filepath):
            self.mpv.command('loadfile', filepath, 'replace')

    def frameStep(self) -> None:
        self.mpv.command('frame-step')

    def frameBackStep(self) -> None:
        self.mpv.command('frame-back-step')

    def seek(self, pos, method='absolute+exact') -> None:
        self.mpv.command('seek', pos, method)

    def pause(self) -> None:
        self.mpv.set_property('pause', not self.mpv.get_property('pause'))

    def mute(self) -> None:
        self.mpv.set_property('mute', not self.mpv.get_property('mute'))

    def volume(self, vol: int) -> None:
        self.mpv.set_property('volume', vol)

    def codec(self, stream: str='video') -> str:
        return self.mpv.get_property('{}-codec'.format(stream))

    def format(self, stream: str='video') -> str:
        return self.mpv.get_property('audio-codec-name' if stream == 'audio' else 'video-format')

    def property(self, prop: str):
        return self.mpv.get_property(prop)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.WindowStateChange and self.isFullScreen():
            self.mpv.set_option('osd-align-x', 'center')
            self.showText('Press ESC key to exit full screen')
            QTimer.singleShot(5000, self.resetOSD)

    def resetOSD(self) -> None:
        self.showText('')
        self.mpv.set_option('osd-align-x', 'left')

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {Qt.Key_F, Qt.Key_Escape}:
            event.accept()
            if self.parent is None:
                self.originalParent.toggleFullscreen()
            else:
                self.parent.toggleFullscreen()
        elif self.isFullScreen():
            self.originalParent.keyPressEvent(event)
        else:
            super(mpvWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        event.accept()
        if event.button() == Qt.LeftButton:
            if self.parent is None:
                self.originalParent.playMedia()
            else:
                self.parent.playMedia()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        event.accept()
        if self.parent is None:
            self.originalParent.toggleFullscreen()
        else:
            self.parent.toggleFullscreen()

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.parent.seekSlider.wheelEvent(event)
