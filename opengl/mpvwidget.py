#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import locale
import signal
import sys

from PyQt5.QtCore import Qt, QMetaObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QSurfaceFormat, QOpenGLContext, QOpenGLVersionProfile
from PyQt5.QtWidgets import qApp, QApplication, QOpenGLWidget

import mpv


class MPVWidget(QOpenGLWidget):
    durationChanged = pyqtSignal(int)
    positionChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        super(MPVWidget, self).__init__(parent, **kwargs)

        self.mpv = mpv.Context()
        self.mpv.initialize()
        self.init_mpv_opts()

        self.gl = self.mpv.opengl_cb_api()
        # self.gl.init_gl(None, gpa)

        if not self.gl:
            raise RuntimeError('OpenGL is not compiled in')

        self.gl.set_update_callback(self.on_update)
        self.frameSwapped.connect(self.swapped)

        self.mpv.observe_property('duration')
        self.mpv.observe_property('time-pos')

        self.mpv.set_wakeup_callback(self.gl)

    def init_mpv_opts(self):
        self.mpv.set_option('terminal', True)
        self.mpv.set_option('msg-level', 'all=v')
        self.mpv.set_option('vo', 'opengl-cb')
        self.mpv.set_option('hwdec', 'auto')
        self.mpv.set_property('video-sync', 'display-vdrop')
        self.mpv.set_property('audio-file-auto', False)
        self.mpv.set_property('quiet', True)

    def initializeGL(self):
        vp = QOpenGLVersionProfile()
        vp.setVersion(2, 1)
        vp.setProfile(QSurfaceFormat.CoreProfile)
        self.local_gl = self.context().versionFunctions(vp)
        self.local_gl.initializeOpenGLFunctions()


    def paintGL(self):
        if self.gl:
            self.gl.draw(0, self.width(), -self.height())

    # def get_proc_address(self, name):
    #     self.makeCurrent()
    #     return self.getProcAddress(name)

    @staticmethod
    def wakeup(ctx):
        QMetaObject.invokeMethod(ctx, 'on_mpv_events', Qt.QueuedConnection)

    @pyqtSlot()
    def swapped(self):
        if self.gl:
            self.gl.report_flip(0)

    def on_mpv_events(self):
        while True:
            event = self.mpv.wait_event(0)
            if event.id == mpv.Events.none:
                break
            if event.id == mpv.Events.get_property_reply:
                event_prop = event.data
                if event_prop.name == 'time-pos':
                    self.positionChanged.emit(event_prop)
                elif event_prop.name == 'duration':
                    self.durationChanged.emit(event_prop)

    def maybeUpdate(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.swapped()
            self.doneCurrent()
        else:
            self.update()

    def on_update(self, ctx):
        QMetaObject.invokeMethod(ctx, 'maybeUpdate')

    def shutdown(self):
        if self.gl:
            self.gl.uninit_gl()
        self.mpv.shutdown()


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    app = QApplication(sys.argv)

    locale.setlocale(locale.LC_NUMERIC, 'C')
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    glwidget = MPVWidget()
    glwidget.show()

    sys.exit(app.exec_())
