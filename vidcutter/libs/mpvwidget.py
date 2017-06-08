#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################################
#
# VidCutter - media cutter & joiner
#
# copyright © 2017 Pete Alexandrou
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

from ctypes import cast, c_void_p

# this is required for Ubuntu which seems to
# have a broken PyQt5 OpenGL implementation
# noinspection PyUnresolvedReferences
from OpenGL import GL

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtOpenGL import QGLContext
from PyQt5.QtWidgets import QOpenGLWidget

from vidcutter.libs.mpv.templates import templateqt


def get_proc_address(ctx, name):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return None
    # noinspection PyTypeChecker
    return int(glctx.getProcAddress(str(name, 'utf-8')))


class mpvWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(mpvWidget, self).__init__(parent)
        self.mpv = mpv(
            parent=self,
            vo='opengl-cb',
            ytdl=False,
            pause=True,
            keep_open=True,
            idle=True,
            osc=False,
            osd_font='Futura LT',
            osd_level=0,
            osd_align_x='left',
            osd_align_y='top',
            cursor_autohide=False,
            input_cursor=False,
            input_default_bindings=False,
            stop_playback_on_init_failure=False,
            input_vo_keyboard=False,
            sub_auto=False,
            sid=False,
            hr_seek=False,
            hr_seek_framedrop=True,
            video_sync='display-vdrop',
            audio_file_auto=False,
            quiet=True,
            terminal=True,
            observe=['time-pos', 'duration'])
        self.mpv.get_opengl_api()
        self.mpv.opengl_set_update_callback(self.updateHandler)
        # ignore expection thrown by older versions of libmpv that do not implement the option
        try:
            self.mpv.set_option('opengl-hwdec-interop', 'auto')
        except:
            pass
        self.frameSwapped.connect(self.swapped)

    def __del__(self):
        self.makeCurrent()
        self.mpv.opengl_set_update_callback(cast(None, c_void_p))
        self.mpv.opengl_uninit_gl()

    def initializeGL(self):
        self.mpv.opengl_init_gl(get_proc_address)

    def paintGL(self):
        self.mpv.opengl_draw(self.defaultFramebufferObject(), self.width(), -self.height())

    @pyqtSlot()
    def swapped(self, do_update: bool = True):
        self.mpv.opengl_report_flip()
        if do_update:
            self.updateHandler()

    def updateHandler(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.swapped(False)
            self.doneCurrent()
        else:
            self.update()


class mpv(templateqt.MpvTemplatePyQt):
    durationChanged = pyqtSignal(float, int)
    positionChanged = pyqtSignal(float, int)

    def on_property_change(self, event):
        if event.data is None:
            return
        if event.name == 'time-pos':
            self.positionChanged.emit(event.data, self.estimated_frame_number)
        elif event.name == 'duration':
            self.durationChanged.emit(event.data, self.estimated_frame_count)
