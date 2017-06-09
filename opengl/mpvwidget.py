#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from ctypes import cast, c_void_p

# this is required for Ubuntu which seems to
# have a broken PyQt5 OpenGL implementation
# noinspection PyUnresolvedReferences
from OpenGL import GL

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtOpenGL import QGLContext
from PyQt5.QtWidgets import QOpenGLWidget

import mpv


def get_proc_address(proc):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return None
    # noinspection PyTypeChecker
    return int(glctx.getProcAddress(str(proc, 'utf-8')))


class mpvWidget(QOpenGLWidget):
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)

    def __init__(self, parent=None, **mpv_opts):
        super(mpvWidget, self).__init__(parent)
        self.setMinimumSize(800, 600)
        self.mpv = mpv.Context()

        def _istr(o):
            return ('yes' if o else 'no') if type(o) is bool else str(o)

        # do not break on non-existant properties/options
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

        self.mpv.observe_property('time-pos')
        self.mpv.observe_property('duration')
        self.mpv.set_wakeup_callback(self.eventHandler)

    def __del__(self):
        self.makeCurrent()
        self._event_thread.stop()
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
            event = self.mpv.wait_event(.01)
            if event.id == mpv.Events.none:
                continue
            elif event.id == mpv.Events.shutdown:
                break
            elif event.id == mpv.Events.property_change:
                event_prop = event.data
                if event_prop.name == 'time-pos':
                    self.positionChanged.emit(int(event_prop.data * 1000))
                elif event_prop.name == 'duration':
                    self.durationChanged.emit(int(event_prop.data * 1000))

    def play(self, file):
        if not os.path.exists(file):
            return
        self.mpv.command('loadfile', file)

    @pyqtSlot(int)
    def seek(self, pos):
        self.mpv.command('seek', pos / 1000, 'absolute+exact')
