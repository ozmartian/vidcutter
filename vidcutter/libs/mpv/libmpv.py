import locale
import logging
import sys

from ctypes import (CDLL, POINTER, RTLD_GLOBAL, addressof, cast, c_int,
                    c_ulong, c_void_p, c_char_p, c_ulonglong, c_double,
                    py_object, pointer)
from ctypes.util import find_library

from .types import (MpvHandle, ErrorCode, Format, MpvEvent, EventID,
                    MpvNode, WakeupCallback, NodeBuilder, SubApi,
                    MpvOpenGLCbContext, OpenGlCbUpdateFn,
                    OpenGlCbGetProcAddrFn)
from .exceptions import MpvError, LibraryNotLoadedError


log = logging.getLogger(__name__)


def load_lua(name='liblua.so'):
    """Use this function if you intend to use mpv's built-in lua interpreter.
    This is e.g. needed for playback of youtube urls.

    """
    CDLL(name, mode=RTLD_GLOBAL)


def _wakeup(ctx):
    libmpv = cast(ctx, POINTER(py_object)).contents.value
    libmpv._wakeup_callback_function(libmpv._wakeup_callback_data)


class LibMPV(object):
    def __init__(self, name=None):
        self.backend = None
        self._wakeup_callback_function = None
        self._wakeup_callback_data = None
        try:
            self.load_library(name)
        except OSError as e:
            raise LibraryNotLoadedError(str(e))
        else:
            self.initialize()

    def client_api_version(self):
        ver = self.backend.mpv_client_api_version()
        return (ver >> 16, ver & 0xFFFF)

    def load_library(self, name=None):
        locale.setlocale(locale.LC_NUMERIC, 'C')
        sharedlib = find_library(name if name is not None
                                 else ('mpv-1.dll' if sys.platform == 'win32' else 'mpv'))
        # hack for AppImage portable apps to work in Linux
        if sharedlib is None and sys.platform.startswith('linux'):
            self.backend = CDLL('libmpv.so.1')
        else:
            self.backend = CDLL(sharedlib)

    def initialize(self):
        self.backend.mpv_client_api_version.restype = c_ulong

        self.backend.mpv_free.argtypes = [c_void_p]
        self.mpv_free = self.backend.mpv_free

        self.backend.mpv_create.restype = MpvHandle
        self.mpv_create = self.backend.mpv_create

        self.backend.mpv_free_node_contents.argtypes = [POINTER(MpvNode)]
        self.mpv_free_node_contents = self.backend.mpv_free_node_contents

        self.backend.mpv_free.argtypes = [c_void_p]
        self.mpv_free = self.backend.mpv_free

        self.backend.mpv_create.restype = MpvHandle
        self.mpv_create = self.backend.mpv_create

        self.backend.mpv_free_node_contents.argtypes = [POINTER(MpvNode)]
        self.mpv_free_node_contents = self.backend.mpv_free_node_contents

        self.backend.mpv_event_name.restype = c_char_p
        self.backend.mpv_event_name.argtypes = [c_int]
        self.mpv_event_name = self.backend.mpv_event_name

        self.backend.mpv_error_string.restype = c_char_p
        self.backend.mpv_error_string.argtypes = [c_int]
        self.mpv_error_string = self.backend.mpv_error_string

        def _handle_func(name, args=[], res=None, ctx=[MpvHandle]):
            func = getattr(self.backend, name)
            if res is not None:
                func.restype = res
            func.argtypes = ctx + args

            def wrapper(*args):
                if res is not ErrorCode:
                    return func(*args)
                result = func(*args)
                if result.value >= 0:
                    return result.value
                # error
                reason = self.mpv_error_string(result.value).decode()
                out_args = []
                for x in args:
                    if type(x) is bytes:
                        out_args.append(x.decode())
                    elif isinstance(x, type(cast(0, POINTER(MpvNode)))):
                        out_args.append(x.contents.get_value())
                    else:
                        out_args.append(x)
                raise MpvError(func.__name__, result, reason, out_args)

            setattr(self, name, wrapper)

        _handle_func('mpv_create_client', [c_char_p], MpvHandle)
        _handle_func('mpv_client_name', [], c_char_p)
        _handle_func('mpv_initialize', [], ErrorCode)
        _handle_func('mpv_detach_destroy', [], c_int)
        _handle_func('mpv_terminate_destroy', [], c_int)
        _handle_func('mpv_load_config_file', [c_char_p], ErrorCode)
        _handle_func('mpv_suspend')
        _handle_func('mpv_resume')
        _handle_func('mpv_get_time_us', [], c_ulonglong)
        _handle_func('mpv_wait_async_requests')
        _handle_func('mpv_set_option', [c_char_p, Format, c_void_p],
                     ErrorCode)
        _handle_func('mpv_set_option_string', [c_char_p, c_char_p], ErrorCode)
        _handle_func('mpv_command', [POINTER(c_char_p)], ErrorCode)
        _handle_func('mpv_command_string', [c_char_p], ErrorCode)
        _handle_func('mpv_command_async', [c_ulonglong, POINTER(c_char_p)],
                     ErrorCode)
        _handle_func('mpv_command_node', [POINTER(MpvNode), POINTER(MpvNode)],
                     ErrorCode)
        _handle_func('mpv_set_property', [c_char_p, Format, c_void_p],
                     ErrorCode)
        _handle_func('mpv_set_property_string', [c_char_p, c_char_p],
                     ErrorCode)
        _handle_func('mpv_set_property_async', [c_ulonglong, c_char_p,
                                                Format, c_void_p],
                     ErrorCode)
        _handle_func('mpv_get_property', [c_char_p, Format, c_void_p],
                     ErrorCode)
        _handle_func('mpv_get_property_string', [c_char_p], c_char_p)
        _handle_func('mpv_get_property_osd_string', [c_char_p], c_char_p)
        _handle_func('mpv_get_property_async', [c_ulonglong, c_char_p,
                                                Format], ErrorCode)
        _handle_func('mpv_observe_property', [c_ulonglong, c_char_p,
                                              Format], ErrorCode)
        _handle_func('mpv_unobserve_property', [c_ulonglong], ErrorCode)
        _handle_func('mpv_request_event', [EventID, c_int], ErrorCode)
        _handle_func('mpv_request_log_messages', [c_char_p], ErrorCode)
        _handle_func('mpv_wait_event', [c_double], POINTER(MpvEvent))
        _handle_func('mpv_wakeup', [], c_int)
        _handle_func('mpv_set_wakeup_callback', [WakeupCallback, c_void_p])
        _handle_func('mpv_get_wakeup_pipe', [], c_int)
        _handle_func('mpv_get_sub_api', [SubApi], c_void_p)

        def _handle_func_cb(name, args=[], res=None):
            return _handle_func(name, args, res, [MpvOpenGLCbContext])

        _handle_func_cb('mpv_opengl_cb_set_update_callback', [OpenGlCbUpdateFn,
                                                              c_void_p])
        _handle_func_cb('mpv_opengl_cb_init_gl', [c_char_p,
                                                  OpenGlCbGetProcAddrFn,
                                                  c_void_p], ErrorCode)
        _handle_func_cb('mpv_opengl_cb_draw', [c_int, c_int, c_int], c_int)
        _handle_func_cb('mpv_opengl_cb_render', [c_int, c_int], c_int)
        _handle_func_cb('mpv_opengl_cb_report_flip', [c_ulonglong], ErrorCode)
        _handle_func_cb('mpv_opengl_cb_uninit_gl', [], ErrorCode)

    def opengl_get_sub_api(self, ctx):
        return cast(self.mpv_get_sub_api(ctx, SubApi.MPV_SUB_API_OPENGL_CB), POINTER(MpvOpenGLCbContext))

    def opengl_cb_set_update_callback(self, ctx, callback, callback_ctx):
        callback = OpenGlCbUpdateFn(callback)
        cb_ctx = cast(pointer(py_object(callback_ctx)), c_void_p)
        self.mpv_opengl_cb_set_update_callback(ctx, callback, cb_ctx)

    def opengl_cb_init_gl(self, ctx, exts, get_proc_address, get_proc_address_ctx):
        proc_address_fn = OpenGlCbGetProcAddrFn(get_proc_address)
        proc_address_ctx = cast(pointer(py_object(get_proc_address_ctx)), c_void_p)
        exts = cast(None, c_char_p)
        self.mpv_opengl_cb_init_gl(ctx, exts, proc_address_fn, proc_address_ctx)

    def opengl_cb_report_flip(self, ctx):
        self.mpv_opengl_cb_report_flip(ctx, 0)

    def opengl_draw(self, ctx, fbo, w, h):
        self.mpv_opengl_cb_draw(ctx, fbo, w, h)

    def opengl_cb_uninit_gl(self, ctx):
        self.mpv_opengl_cb_uninit_gl(ctx)

    def set_wakeup_callback(self, ctx, func, d):
        if self._wakeup_callback_function is not None:
            return
        self._wakeup_callback_function = func
        self._wakeup_callback_data = d
        wakeup = WakeupCallback(_wakeup)
        wakeup_data = cast(pointer(py_object(self)), c_void_p)

        self.mpv_set_wakeup_callback(ctx, wakeup, wakeup_data)

    def command(self, ctx, *args):
        """ Execute a raw command """
        args = [str(arg).encode() for arg in args if arg is not None] + [None]
        self.mpv_command(ctx, (c_char_p * len(args))(*args))

    def command_node(self, ctx, *args):
        """Send a command with an MpvNode instead of strings."""
        nb = NodeBuilder(args)
        res = MpvNode()
        self.mpv_command_node(ctx, cast(addressof(nb.node), POINTER(MpvNode)),
                              cast(addressof(res), POINTER(MpvNode)))
        data = res.get_value()
        self.mpv_free_node_contents(cast(addressof(res), POINTER(MpvNode)))
        return data

    def set_option(self, ctx, name, v):
        nb = NodeBuilder(v)
        self.mpv_set_option(ctx, name.encode(), Format.NODE,
                            cast(addressof(nb.node), POINTER(MpvNode)))

    def _get_property(self, ctx, prop, mpv_format):
        if mpv_format == Format.NONE:
            raise TypeError
        ctype = Format(mpv_format).ctype()
        res = ctype()
        self.mpv_get_property(ctx, prop.encode(), mpv_format, addressof(res))

        data = Format(mpv_format).decode(res)
        if mpv_format in [Format.STRING, Format.OSD_STRING]:
            self.mpv_free(res)
        elif mpv_format == Format.NODE:
            self.mpv_free_node_contents(cast(addressof(res), POINTER(MpvNode)))

        return data

    def _set_property(self, ctx, prop, mpv_format, value):
        if mpv_format == Format.NONE:
            raise TypeError
        val = Format(mpv_format).encode(value)
        self.mpv_set_property(ctx, prop.encode(), mpv_format, addressof(val))
