#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from ctypes import cast, c_void_p

# this is required for Ubuntu which seems to
# have a broken PyQt5 OpenGL implementation
from OpenGL import GL

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtOpenGL import QGLContext
from PyQt5.QtWidgets import QOpenGLWidget

import mpv


def get_proc_address(proc):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return None
    return int(glctx.getProcAddress(str(proc, 'utf-8')))


class mpvWidget(QOpenGLWidget):
    def __init__(self, parent=None, observe=list(), **mpv_opts):
        super(mpvWidget, self).__init__(parent)
        self.mpv = mpv.Context()

        def _istr(o):
            return ('yes' if o else 'no') if type(o) is bool else str(o)

        for prop in observe:
            self.mpv.observe_property(prop)
        for opt, val in mpv_opts.items():
            try:
                self.mpv.set_option(opt.replace('_', '-'), _istr(val))
            except:
                pass
        self.mpv.initialize()
        self.opengl = self.mpv.opengl_cb_api()
        self.opengl.set_update_callback(self.updateHandler)
        # ignore expection thrown by older versions of libmpv that do not implement the option
        try:
            self.mpv.set_option('opengl-hwdec-interop', 'auto')
            if sys.platform == 'win32':
                self.mpv.set_option('opengl-backend', 'angle')
        except:
            pass
        self.frameSwapped.connect(self.swapped, Qt.DirectConnection)

    def __del__(self):
        self.makeCurrent()
        if hasattr(self, 'opengl'):
            self.opengl.set_update_callback(cast(None, c_void_p))
            self.opengl.uninit_gl()
        self.mpv.shutdown()

    def initializeGL(self):
        if self.opengl:
            self.opengl.init_gl(None, get_proc_address)

    def paintGL(self):
        if self.opengl:
            self.opengl.draw(self.defaultFramebufferObject(), self.width(), -self.height())

    @pyqtSlot()
    def swapped(self, update: bool = True):
        if self.opengl:
            self.opengl.report_flip(0)

    @pyqtSlot()
    def updateHandler(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.swapped(False)
            self.doneCurrent()
        else:
            self.update()

# class Mpv(mpv.templates.MpvTemplatePyQt):
#     durationChanged = pyqtSignal(int)
#     positionChanged = pyqtSignal(int)
#
#     def on_property_change(self, event):
#         if event.data is None:
#             return
#         if event.name == 'time-pos':
#             self.positionChanged.emit(int(event.data))
#         elif event.name == 'duration':
#             self.durationChanged.emit(int(event.data))
