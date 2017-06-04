#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ctypes import cast, c_void_p

# this is required for Ubuntu which seems to
# have a broken PyQt5 OpenGL implementation
from OpenGL import GL

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QMetaObject, Qt
from PyQt5.QtOpenGL import QGLContext
from PyQt5.QtWidgets import QOpenGLWidget

import mpv.templates


def get_proc_address(ctx, proc):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return None
    return int(glctx.getProcAddress(str(proc, 'utf-8')))


class MpvWidget(QOpenGLWidget):
    updated = pyqtSignal()

    def __init__(self, parent=None):
        super(MpvWidget, self).__init__(parent)
        self.mpv = Mpv(
            pause=True,
            terminal=True,
            msg_level='all=v',
            vo='opengl-cb',
            hwdec='auto',
            hr_seek=False,
            hr_seek_framedrop=True,
            video_sync='display-vdrop',
            audio_file_auto=False,
            quiet=True,
            keep_open=True,
            idle=True,
            observe=['time-pos', 'duration'])
        self.mpv.get_opengl_api()
        self.mpv.opengl_set_update_callback(MpvWidget.on_update)
        # ignore expection thrown by older versions of libmpv that do not implement the option
        try:
            self.mpv.set_option('opengl-hwdec-interop', 'auto')
        except:
            pass
        self.frameSwapped.connect(self.swapped, Qt.DirectConnection)
        self.updated.connect(self.updateHandler, Qt.QueuedConnection)

    def __del__(self):
        self.makeCurrent()
        self.mpv.opengl_set_update_callback(cast(None, c_void_p))
        self.mpv.opengl_uninit_gl()

    def initializeGL(self):
        self.mpv.opengl_init_gl(get_proc_address)

    def paintGL(self):
        self.mpv.opengl_draw(self.defaultFramebufferObject(), self.width(), -self.height())

    @pyqtSlot()
    def swapped(self):
        self.mpv.opengl_report_flip()
        self.updated.emit()

    @staticmethod
    def on_update(ctx):
        if isinstance(ctx, MpvWidget):
            ctx.updated.emit()

    @pyqtSlot()
    def updateHandler(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.swapped()
            self.doneCurrent()
        else:
            self.update()


class Mpv(mpv.templates.MpvTemplatePyQt):
    durationChanged = pyqtSignal(int)
    positionChanged = pyqtSignal(int)

    def on_property_change(self, event):
        if event.data is None:
            return
        if event.name == 'time-pos':
            self.positionChanged.emit(int(event.data))
        elif event.name == 'duration':
            self.durationChanged.emit(int(event.data))
