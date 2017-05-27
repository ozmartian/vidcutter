#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Python MPV library module
# Copyright (C) 2017 Sebastian Götte <code@jaseg.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import collections
import ctypes.util
import os
import re
import sys
import threading
import traceback
from ctypes import *
from functools import partial, wraps

# vim: ts=4 sw=4 et

if os.name == 'nt':
    backend = CDLL('mpv-1.dll')
    fs_enc = 'utf-8'
else:
    import locale

    lc, enc = locale.getlocale(locale.LC_NUMERIC)
    # libmpv requires LC_NUMERIC to be set to "C". Since messing with global variables everyone else relies upon is
    # still better than segfaulting, we are setting LC_NUMERIC to "C".
    locale.setlocale(locale.LC_NUMERIC, 'C')

    sofile = ctypes.util.find_library('mpv')

    # need this hack for AppImage bundles to work
    if sofile is None:
        sofile = 'libmpv.so.1'

    backend = CDLL(sofile)

    # commenting this out so th original exception can be thrown and thus caught/handled accordingly
    #
    # try:
    #     backend = CDLL(sofile)
    # except OSError:
    #     raise OSError("Cannot find libmpv in the usual places. Depending on your distro, you may try installing an "
    #             "mpv-devel or mpv-libs package. If you have libmpv around but this script can't find it, maybe consult "
    #             "the documentation for ctypes.util.find_library which this script uses to look up the library "
    #             "media.")

    fs_enc = sys.getfilesystemencoding()


class MpvHandle(c_void_p):
    pass


class MpvOpenGLCbContext(c_void_p):
    pass


class PropertyUnavailableError(AttributeError):
    pass


class ErrorCode(object):
    """ For documentation on these, see mpv's libmpv/client.h """
    SUCCESS = 0
    EVENT_QUEUE_FULL = -1
    NOMEM = -2
    UNINITIALIZED = -3
    INVALID_PARAMETER = -4
    OPTION_NOT_FOUND = -5
    OPTION_FORMAT = -6
    OPTION_ERROR = -7
    PROPERTY_NOT_FOUND = -8
    PROPERTY_FORMAT = -9
    PROPERTY_UNAVAILABLE = -10
    PROPERTY_ERROR = -11
    COMMAND = -12

    EXCEPTION_DICT = {
        0: None,
        -1: lambda *a: MemoryError('mpv event queue full', *a),
        -2: lambda *a: MemoryError('mpv cannot allocate memory', *a),
        -3: lambda *a: ValueError('Uninitialized mpv handle used', *a),
        -4: lambda *a: ValueError('Invalid value for mpv parameter', *a),
        -5: lambda *a: AttributeError('mpv option does not exist', *a),
        -6: lambda *a: TypeError('Tried to set mpv option using wrong format', *a),
        -7: lambda *a: ValueError('Invalid value for mpv option', *a),
        -8: lambda *a: AttributeError('mpv property does not exist', *a),
        # Currently (mpv 0.18.1) there is a bug causing a PROPERTY_FORMAT error to be returned instead of
        # INVALID_PARAMETER when setting a property-mapped option to an invalid value.
        -9: lambda *a: TypeError('Tried to get/set mpv property using wrong format, or passed invalid value', *a),
        -10: lambda *a: PropertyUnavailableError('mpv property is not available', *a),
        -11: lambda *a: RuntimeError('Generic error getting or setting mpv property', *a),
        -12: lambda *a: SystemError('Error running mpv command', *a)}

    @staticmethod
    def default_error_handler(ec, *args):
        return ValueError(_mpv_error_string(ec).decode('utf-8'), ec, *args)

    @classmethod
    def raise_for_ec(kls, ec, func, *args):
        ec = 0 if ec > 0 else ec
        ex = kls.EXCEPTION_DICT.get(ec, kls.default_error_handler)
        if ex:
            raise ex(ec, *args)


class MpvFormat(c_int):
    NONE = 0
    STRING = 1
    OSD_STRING = 2
    FLAG = 3
    INT64 = 4
    DOUBLE = 5
    NODE = 6
    NODE_ARRAY = 7
    NODE_MAP = 8
    BYTE_ARRAY = 9

    def __eq__(self, other):
        return self is other or self.value == other or self.value == int(other)

    def __repr__(self):
        return ['NONE', 'STRING', 'OSD_STRING', 'FLAG', 'INT64', 'DOUBLE', 'NODE', 'NODE_ARRAY', 'NODE_MAP',
                'BYTE_ARRAY'][self.value]

    def __hash__(self):
        return self.value


class MpvEventID(c_int):
    NONE = 0
    SHUTDOWN = 1
    LOG_MESSAGE = 2
    GET_PROPERTY_REPLY = 3
    SET_PROPERTY_REPLY = 4
    COMMAND_REPLY = 5
    START_FILE = 6
    END_FILE = 7
    FILE_LOADED = 8
    TRACKS_CHANGED = 9
    TRACK_SWITCHED = 10
    IDLE = 11
    PAUSE = 12
    UNPAUSE = 13
    TICK = 14
    SCRIPT_INPUT_DISPATCH = 15
    CLIENT_MESSAGE = 16
    VIDEO_RECONFIG = 17
    AUDIO_RECONFIG = 18
    METADATA_UPDATE = 19
    SEEK = 20
    PLAYBACK_RESTART = 21
    PROPERTY_CHANGE = 22
    CHAPTER_CHANGE = 23

    ANY = (SHUTDOWN, LOG_MESSAGE, GET_PROPERTY_REPLY, SET_PROPERTY_REPLY, COMMAND_REPLY, START_FILE, END_FILE,
           FILE_LOADED, TRACKS_CHANGED, TRACK_SWITCHED, IDLE, PAUSE, UNPAUSE, TICK, SCRIPT_INPUT_DISPATCH,
           CLIENT_MESSAGE, VIDEO_RECONFIG, AUDIO_RECONFIG, METADATA_UPDATE, SEEK, PLAYBACK_RESTART, PROPERTY_CHANGE,
           CHAPTER_CHANGE)

    def __repr__(self):
        return ['NONE', 'SHUTDOWN', 'LOG_MESSAGE', 'GET_PROPERTY_REPLY', 'SET_PROPERTY_REPLY', 'COMMAND_REPLY',
                'START_FILE', 'END_FILE', 'FILE_LOADED', 'TRACKS_CHANGED', 'TRACK_SWITCHED', 'IDLE', 'PAUSE', 'UNPAUSE',
                'TICK', 'SCRIPT_INPUT_DISPATCH', 'CLIENT_MESSAGE', 'VIDEO_RECONFIG', 'AUDIO_RECONFIG',
                'METADATA_UPDATE', 'SEEK', 'PLAYBACK_RESTART', 'PROPERTY_CHANGE', 'CHAPTER_CHANGE'][self.value]

    @classmethod
    def from_str(kls, s):
        return getattr(kls, s.upper().replace('-', '_'))


class MpvNodeList(Structure):
    def array_value(self, decode_str=False):
        return [self.values[i].node_value(decode_str) for i in range(self.num)]

    def dict_value(self, decode_str=False):
        return {self.keys[i].decode('utf-8'): self.values[i].node_value(decode_str) for i in range(self.num)}


class MpvNode(Structure):
    _fields_ = [('val', c_longlong),
                ('format', MpvFormat)]

    def node_value(self, decode_str=False):
        return MpvNode.node_cast_value(byref(c_void_p(self.val)), self.format.value, decode_str)

    @staticmethod
    def node_cast_value(v, fmt, decode_str=False):
        dwrap = lambda s: s.decode('utf-8') if decode_str else s
        return {
            MpvFormat.NONE: lambda v: None,
            MpvFormat.STRING: lambda v: dwrap(cast(v, POINTER(c_char_p)).contents.value),
            MpvFormat.OSD_STRING: lambda v: cast(v, POINTER(c_char_p)).contents.value.decode('utf-8'),
            MpvFormat.FLAG: lambda v: bool(cast(v, POINTER(c_int)).contents.value),
            MpvFormat.INT64: lambda v: cast(v, POINTER(c_longlong)).contents.value,
            MpvFormat.DOUBLE: lambda v: cast(v, POINTER(c_double)).contents.value,
            MpvFormat.NODE: lambda v: cast(v, POINTER(MpvNode)).contents.node_value(decode_str),
            MpvFormat.NODE_ARRAY: lambda v: cast(v, POINTER(POINTER(MpvNodeList))).contents.contents.array_value(
                decode_str),
            MpvFormat.NODE_MAP: lambda v: cast(v, POINTER(POINTER(MpvNodeList))).contents.contents.dict_value(
                decode_str),
            MpvFormat.BYTE_ARRAY: lambda v: cast(v, POINTER(c_char_p)).contents.value,
        }[fmt](v)


MpvNodeList._fields_ = [('num', c_int),
                        ('values', POINTER(MpvNode)),
                        ('keys', POINTER(c_char_p))]


class MpvSubApi(c_int):
    MPV_SUB_API_OPENGL_CB = 1


class MpvEvent(Structure):
    _fields_ = [('event_id', MpvEventID),
                ('error', c_int),
                ('reply_userdata', c_ulonglong),
                ('data', c_void_p)]

    def as_dict(self):
        dtype = {MpvEventID.END_FILE: MpvEventEndFile,
                 MpvEventID.PROPERTY_CHANGE: MpvEventProperty,
                 MpvEventID.GET_PROPERTY_REPLY: MpvEventProperty,
                 MpvEventID.LOG_MESSAGE: MpvEventLogMessage,
                 MpvEventID.SCRIPT_INPUT_DISPATCH: MpvEventScriptInputDispatch,
                 MpvEventID.CLIENT_MESSAGE: MpvEventClientMessage
                 }.get(self.event_id.value, None)
        return {'event_id': self.event_id.value,
                'error': self.error,
                'reply_userdata': self.reply_userdata,
                'event': cast(self.data, POINTER(dtype)).contents.as_dict() if dtype else None}


class MpvEventProperty(Structure):
    _fields_ = [('name', c_char_p),
                ('format', MpvFormat),
                ('data', c_void_p)]

    def as_dict(self, decode_str=False):
        proptype, _access = ALL_PROPERTIES.get(self.name, (str, None))
        value = MpvNode.node_cast_value(self.data, self.format.value, decode_str or proptype in (str, _commalist))
        return {'name': self.name.decode('utf-8'),
                'format': self.format,
                'data': self.data,
                'value': value}


class MpvEventLogMessage(Structure):
    _fields_ = [('prefix', c_char_p),
                ('level', c_char_p),
                ('text', c_char_p)]

    def as_dict(self):
        return {'prefix': self.prefix.decode('utf-8'),
                'level': self.level.decode('utf-8'),
                'text': self.text.decode('utf-8').rstrip()}


class MpvEventEndFile(c_int):
    EOF_OR_INIT_FAILURE = 0
    RESTARTED = 1
    ABORTED = 2
    QUIT = 3

    def as_dict(self):
        return {'reason': self.value}


class MpvEventScriptInputDispatch(Structure):
    _fields_ = [('arg0', c_int),
                ('type', c_char_p)]

    def as_dict(self):
        pass  # TODO


class MpvEventClientMessage(Structure):
    _fields_ = [('num_args', c_int),
                ('args', POINTER(c_char_p))]

    def as_dict(self):
        return {'args': [self.args[i].decode('utf-8') for i in range(self.num_args)]}


WakeupCallback = CFUNCTYPE(None, c_void_p)

OpenGlCbUpdateFn = CFUNCTYPE(None, c_void_p)
OpenGlCbGetProcAddrFn = CFUNCTYPE(None, c_void_p, c_char_p)


def _handle_func(name, args, restype, errcheck, ctx=MpvHandle):
    func = getattr(backend, name)
    func.argtypes = [ctx] + args if ctx else args
    if restype is not None:
        func.restype = restype
    if errcheck is not None:
        func.errcheck = errcheck
    globals()['_' + name] = func


def bytes_free_errcheck(res, func, *args):
    notnull_errcheck(res, func, *args)
    rv = cast(res, c_void_p).value
    _mpv_free(res)
    return rv


def notnull_errcheck(res, func, *args):
    if res is None:
        raise RuntimeError('Underspecified error in MPV when calling {} with args {!r}: NULL pointer returned.' \
                           'Please consult your local debugger.'.format(func.__name__, args))
    return res


ec_errcheck = ErrorCode.raise_for_ec


def _handle_gl_func(name, args=[], restype=None):
    _handle_func(name, args, restype, errcheck=None, ctx=MpvOpenGLCbContext)


backend.mpv_client_api_version.restype = c_ulong


def _mpv_client_api_version():
    ver = backend.mpv_client_api_version()
    return ver >> 16, ver & 0xFFFF


backend.mpv_free.argtypes = [c_void_p]
_mpv_free = backend.mpv_free

backend.mpv_free_node_contents.argtypes = [c_void_p]
_mpv_free_node_contents = backend.mpv_free_node_contents

backend.mpv_create.restype = MpvHandle
_mpv_create = backend.mpv_create

_handle_func('mpv_create_client', [c_char_p], MpvHandle, notnull_errcheck)
_handle_func('mpv_client_name', [], c_char_p, errcheck=None)
_handle_func('mpv_initialize', [], c_int, ec_errcheck)
_handle_func('mpv_detach_destroy', [], None, errcheck=None)
_handle_func('mpv_terminate_destroy', [], None, errcheck=None)
_handle_func('mpv_load_config_file', [c_char_p], c_int, ec_errcheck)
_handle_func('mpv_suspend', [], None, errcheck=None)
_handle_func('mpv_resume', [], None, errcheck=None)
_handle_func('mpv_get_time_us', [], c_ulonglong, errcheck=None)

_handle_func('mpv_set_option', [c_char_p, MpvFormat, c_void_p], c_int, ec_errcheck)
_handle_func('mpv_set_option_string', [c_char_p, c_char_p], c_int, ec_errcheck)

_handle_func('mpv_command', [POINTER(c_char_p)], c_int, ec_errcheck)
_handle_func('mpv_command_string', [c_char_p, c_char_p], c_int, ec_errcheck)
_handle_func('mpv_command_async', [c_ulonglong, POINTER(c_char_p)], c_int, ec_errcheck)

_handle_func('mpv_set_property', [c_char_p, MpvFormat, c_void_p], c_int, ec_errcheck)
_handle_func('mpv_set_property_string', [c_char_p, c_char_p], c_int, ec_errcheck)
_handle_func('mpv_set_property_async', [c_ulonglong, c_char_p, MpvFormat, c_void_p], c_int, ec_errcheck)
_handle_func('mpv_get_property', [c_char_p, MpvFormat, c_void_p], c_int, ec_errcheck)
_handle_func('mpv_get_property_string', [c_char_p], c_void_p, bytes_free_errcheck)
_handle_func('mpv_get_property_osd_string', [c_char_p], c_void_p, bytes_free_errcheck)
_handle_func('mpv_get_property_async', [c_ulonglong, c_char_p, MpvFormat], c_int, ec_errcheck)
_handle_func('mpv_observe_property', [c_ulonglong, c_char_p, MpvFormat], c_int, ec_errcheck)
_handle_func('mpv_unobserve_property', [c_ulonglong], c_int, ec_errcheck)

_handle_func('mpv_event_name', [c_int], c_char_p, errcheck=None, ctx=None)
_handle_func('mpv_error_string', [c_int], c_char_p, errcheck=None, ctx=None)

_handle_func('mpv_request_event', [MpvEventID, c_int], c_int, ec_errcheck)
_handle_func('mpv_request_log_messages', [c_char_p], c_int, ec_errcheck)
_handle_func('mpv_wait_event', [c_double], POINTER(MpvEvent), errcheck=None)
_handle_func('mpv_wakeup', [], None, errcheck=None)
_handle_func('mpv_set_wakeup_callback', [WakeupCallback, c_void_p], None, errcheck=None)
_handle_func('mpv_get_wakeup_pipe', [], c_int, errcheck=None)

_handle_func('mpv_get_sub_api', [MpvSubApi], c_void_p, notnull_errcheck)

_handle_gl_func('mpv_opengl_cb_set_update_callback', [OpenGlCbUpdateFn, c_void_p])
_handle_gl_func('mpv_opengl_cb_init_gl', [c_char_p, OpenGlCbGetProcAddrFn, c_void_p], c_int)
_handle_gl_func('mpv_opengl_cb_draw', [c_int, c_int, c_int], c_int)
_handle_gl_func('mpv_opengl_cb_render', [c_int, c_int], c_int)
_handle_gl_func('mpv_opengl_cb_report_flip', [c_ulonglong], c_int)
_handle_gl_func('mpv_opengl_cb_uninit_gl', [], c_int)


def _ensure_encoding(possibly_bytes):
    return possibly_bytes.decode('utf-8') if type(possibly_bytes) is bytes else possibly_bytes


def _event_generator(handle):
    while True:
        event = _mpv_wait_event(handle, -1).contents
        if event.event_id.value == MpvEventID.NONE:
            raise StopIteration()
        yield event


def load_lua():
    """ Use this function if you intend to use mpv's built-in lua interpreter. This is e.g. needed for playback of
    youtube urls. """
    CDLL('liblua.so', mode=RTLD_GLOBAL)


def _event_loop(event_handle, playback_cond, event_callbacks, message_handlers, property_handlers, log_handler):
    for event in _event_generator(event_handle):
        try:
            devent = event.as_dict()  # copy data from ctypes
            eid = devent['event_id']
            for callback in event_callbacks:
                callback(devent)
            if eid in (MpvEventID.SHUTDOWN, MpvEventID.END_FILE):
                with playback_cond:
                    playback_cond.notify_all()
            if eid == MpvEventID.PROPERTY_CHANGE:
                pc = devent['event']
                name, value, fmt = pc['name'], pc['value'], pc['format']

                for handler in property_handlers[name][fmt]:
                    handler(name, value)
            if eid == MpvEventID.LOG_MESSAGE and log_handler is not None:
                ev = devent['event']
                log_handler(ev['level'], ev['prefix'], ev['text'])
            if eid == MpvEventID.CLIENT_MESSAGE:
                # {'event': {'args': ['key-binding', 'foo', 'u-', 'g']}, 'reply_userdata': 0, 'error': 0, 'event_id': 16}
                target, *args = devent['event']['args']
                if target in message_handlers:
                    message_handlers[target](*args)
            if eid == MpvEventID.SHUTDOWN:
                _mpv_detach_destroy(event_handle)
                return
        except Exception as e:
            traceback.print_exc()


class OSDPropertyProxy:
    def __init__(self, mpv):
        self.mpv = mpv


class MPV(object):
    """ See man mpv(1) for the details of the implemented commands. All mpv
    properties can be accessed as ```my_mpv.some_property``` and all mpv
    options can be accessed as ```my_mpv['some-option']```. """

    def __init__(self, *extra_mpv_flags, log_handler=None, start_event_thread=True, **extra_mpv_opts):
        """ Create an MPV instance.

        Extra arguments and extra keyword arguments will be passed to mpv as options. """

        self._event_thread = None
        self.handle = _mpv_create()

        _mpv_set_option_string(self.handle, b'audio-display', b'no')
        istr = lambda o: ('yes' if o else 'no') if type(o) is bool else str(o)
        try:
            for flag in extra_mpv_flags:
                _mpv_set_option_string(self.handle, flag.encode('utf-8'), b'')
            for k, v in extra_mpv_opts.items():
                _mpv_set_option_string(self.handle, k.replace('_', '-').encode('utf-8'), istr(v).encode('utf-8'))
        finally:
            _mpv_initialize(self.handle)

        self.osd = OSDPropertyProxy(self)
        self._event_callbacks = []
        self._property_handlers = collections.defaultdict(lambda: collections.defaultdict(lambda: []))
        self._message_handlers = {}
        self._key_binding_handlers = {}
        self._playback_cond = threading.Condition()
        self._event_handle = _mpv_create_client(self.handle, b'py_event_handler')
        self._loop = partial(_event_loop, self._event_handle, self._playback_cond, self._event_callbacks,
                             self._message_handlers, self._property_handlers, log_handler)
        if start_event_thread:
            self._event_thread = threading.Thread(target=self._loop, name='MPVEventHandlerThread')
            self._event_thread.setDaemon(True)
            self._event_thread.start()
        else:
            self._event_thread = None

        if log_handler is not None:
            self.set_loglevel('terminal-default')

    def wait_for_playback(self):
        """ Waits until playback of the current title is paused or done """
        with self._playback_cond:
            self._playback_cond.wait()

    def wait_for_property(self, name, cond=lambda val: val, level_sensitive=True):
        """ Waits until ```cond``` evaluates to a truthy value on the named
        property. This can be used to wait for properties such as
        ```idle_active``` indicating the player is done with regular playback
        and just idling around """
        sema = threading.Semaphore(value=0)

        def observer(name, val):
            if cond(val):
                sema.release()

        self.observe_property(name, observer)
        if not level_sensitive or not cond(getattr(self, name.replace('-', '_'))):
            sema.acquire()
        self.unobserve_property(name, observer)

    def __del__(self):
        if self.handle:
            self.terminate()

    def terminate(self):
        """ Pröperly terminates this player instance. Preferably use this
        instead of relying on python's garbage collector to cause this to be
        called from the object's destructor. """
        self.handle, handle = None, self.handle
        if threading.current_thread() is self._event_thread:
            # Handle special case to allow event handle to be detached.
            # This is necessary since otherwise the event thread would deadlock itself.
            grim_reaper = threading.Thread(target=lambda: _mpv_terminate_destroy(handle))
            grim_reaper.start()
        else:
            _mpv_terminate_destroy(handle)
            if self._event_thread:
                self._event_thread.join()

    def set_loglevel(self, level):
        """ Set MPV's log level. This adjusts which output will be sent to this
        object's log handlers. If you just want mpv's regular terminal output,
        you don't need to adjust this but just need to pass a log handler to
        the MPV constructur such as ```MPV(log_handler=print)```.

        Valid log levels are "no", "fatal", "error", "warn", "info", "v"
        "debug" and "trace". For details see your mpv's client.h header file """
        _mpv_request_log_messages(self._event_handle, level.encode('utf-8'))

    def command(self, name, *args):
        """ Execute a raw command """
        args = [name.encode('utf-8')] + [(arg if type(arg) is bytes else str(arg).encode('utf-8'))
                                         for arg in args if arg is not None] + [None]
        _mpv_command(self.handle, (c_char_p * len(args))(*args))

    def seek(self, amount, reference="relative", precision="default-precise"):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('seek', amount, reference, precision)

    def revert_seek(self):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('revert_seek');

    def frame_step(self):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('frame_step')

    def frame_back_step(self):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('frame_back_step')

    def keep_aspect(self, flag):
        self._set_property('keepaspect', flag)

    def _add_property(self, name, value=None):
        self.command('add_property', name, value)

    def _cycle_property(self, name, direction='up'):
        self.command('cycle_property', name, direction)

    def _multiply_property(self, name, factor):
        self.command('multiply_property', name, factor)

    def screenshot(self, includes='subtitles', mode='single'):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('screenshot', includes, mode)

    def screenshot_to_file(self, filename, includes='subtitles'):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('screenshot_to_file', filename.encode(fs_enc), includes)

    def playlist_next(self, mode='weak'):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('playlist_next', mode)

    def playlist_prev(self, mode='weak'):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('playlist_prev', mode)

    @staticmethod
    def _encode_options(options):
        return ','.join('{}={}'.format(str(key), str(val)) for key, val in options.items())

    def loadfile(self, filename, mode='replace', **options):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('loadfile', filename.encode(fs_enc), mode, MPV._encode_options(options))

    def loadlist(self, playlist, mode='replace'):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('loadlist', playlist.encode(fs_enc), mode)

    def playlist_clear(self):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('playlist_clear')

    def playlist_remove(self, index='current'):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('playlist_remove', index)

    def playlist_move(self, index1, index2):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('playlist_move', index1, index2)

    def run(self, command, *args):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('run', command, *args)

    def quit(self, code=None):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('quit', code)

    def quit_watch_later(self, code=None):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('quit_watch_later', code)

    def sub_add(self, filename):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('sub_add', filename.encode(fs_enc))

    def sub_remove(self, sub_id=None):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('sub_remove', sub_id)

    def sub_reload(self, sub_id=None):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('sub_reload', sub_id)

    def sub_step(self, skip):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('sub_step', skip)

    def sub_seek(self, skip):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('sub_seek', skip)

    def toggle_osd(self):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('osd')

    def show_text(self, string, duration='-', level=None):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('show_text', string, duration, level)

    def show_progress(self):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('show_progress')

    def discnav(self, command):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('discnav', command)

    def write_watch_later_config(self):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('write_watch_later_config')

    def overlay_add(self, overlay_id, x, y, file_or_fd, offset, fmt, w, h, stride):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('overlay_add', overlay_id, x, y, file_or_fd, offset, fmt, w, h, stride)

    def overlay_remove(self, overlay_id):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('overlay_remove', overlay_id)

    def script_message(self, *args):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('script_message', *args)

    def script_message_to(self, target, *args):
        """ Mapped mpv seek command, see man mpv(1). """
        self.command('script_message_to', target, *args)

    def observe_property(self, name, handler, *, force_fmt=None):
        """ Register an observer on the named property. An observer is a function that is called with the new property
        value every time the property's value is changed. The basic function signature is ```fun(property_name,
        new_value)``` with new_value being the decoded property value as a python object. This function can be used as a
        function decorator if no handler is given.

        By default, you'll get whatever return type you'd get if you asked the regular property access API. To override
        this behavior, you can specify a forced return type from ```MpvFormat``` in force_fmt

        To uunregister the observer, call either of ```mpv.unobserve_property(name, handler)```,
        ```mpv.unobserve_all_properties(handler)``` or the handler's ```unregister_mpv_properties``` attribute:

        ```
        @player.observe_property('volume')
        def my_handler(new_volume, *):
            print("It's loud!", volume)

        my_handler.unregister_mpv_properties()
        ``` """
        fmt = force_fmt or MpvFormat.NODE
        # handler.observed_mpv_properties = getattr(handler, 'observed_mpv_properties', []) + [name]
        # handler.unregister_mpv_properties = lambda: self.unobserve_property(None, handler)
        self._property_handlers[name][fmt].append(handler)
        _mpv_observe_property(self._event_handle, hash(name) & 0xffffffffffffffff, name.encode('utf-8'), fmt)

    def property_observer(self, name, *, force_fmt=None):
        """ Function decorator to register a property observer. See ```MPV.observe_property``` for details. """

        def wrapper(fun):
            self.observe_property(name, fun, force_fmt=force_fmt)
            fun.unobserve_mpv_properties = lambda: self.unobserve_property(None, fun)
            return fun

        return wrapper

    def unobserve_property(self, name, handler):
        """ Unregister a property observer. This requires both the observed property's name and the handler function
        that was originally registered as one handler could be registered for several properties. To unregister a
        handler from *all* observed properties see ```unobserve_all_properties```. """
        fmts = self._property_handlers[name]
        for fmt, handlers in fmts.items():
            handlers.remove(handler)

        # remove all properties that have no handlers
        empty_props = [
            fmt for fmt, handler in fmts.items() if not handler
        ]

        for fmt in empty_props:
            del fmts[fmt]

        if not fmts:
            _mpv_unobserve_property(self._event_handle, hash(name) & 0xffffffffffffffff)

    def unobserve_all_properties(self, handler):
        """ Unregister a property observer from *all* observed properties. """
        for name in self._property_handlers:
            self.unobserve_property(name, handler)

    def register_message_handler(self, target, handler=None):
        """ Register a mpv script message handler. This can be used to communicate with embedded lua scripts. Pass the
        script message target name this handler should be listening to and the handler function.

        WARNING: Only one handler can be registered at a time for any given target.

        To unregister the message handler, call its unregister_mpv_messages function:

        ```
        player = mpv.MPV()
        @player.message_handler('foo')
        def my_handler(some, args):
            print(args)

        my_handler.unregister_mpv_messages()
        ``` """
        self._register_message_handler_internal(target, handler)

    def _register_script_message_handler_internal(self, target, handler):
        handler.mpv_message_targets = getattr(handler, 'mpv_script_message_targets', []) + [target]
        self._message_handlers[target] = handler

    def unregister_message_handler(self, target_or_handler):
        """ Unregister a mpv script message handler for the given script message target name.

        You can also call the ```unregister_mpv_messages``` function attribute set on the handler function when it is
        registered. """
        if isinstance(target, str):
            del self._message_handlers[target]
        else:
            for key, val in self._message_handlers.items():
                if val == target_or_handler:
                    del self._message_handlers[key]

    def message_handler(self, target):
        """ Decorator to register a mpv script message handler.

        WARNING: Only one handler can be registered at a time for any given target.

        To unregister the message handler, call its unregister_mpv_messages function:

        ```
        player = mpv.MPV()
        @player.message_handler('foo')
        def my_handler(some, args):
            print(args)

        my_handler.unregister_mpv_messages()
        """

        def register(handler):
            self._register_message_handler_internal(target, handler)
            handler.unregister_mpv_messages = lambda: self.unregister_message_handler(handler)
            return handler

        return register

    def register_event_callback(self, callback):
        """ Register a blanket event callback receiving all event types.

        To unregister the event callback, call its unregister_mpv_events function:

        ```
        player = mpv.MPV()
        @player.event_callback('shutdown')
        def my_handler(event):
            print('It ded.')

        my_handler.unregister_mpv_events()
        """
        callback.unregister_mpv_events = partial(self.unregister_event_callback, callback)
        self._event_callbacks.append(callback)

    def unregister_event_callback(self, callback):
        """ Unregiser an event callback. """
        self._event_callbacks.remove(callback)

    def event_callback(self, *event_types):
        """ Function decorator to register a blanket event callback for the given event types. Event types can be given
        as str (e.g.  'start-file'), integer or MpvEventID object.

        WARNING: Due to the way this is filtering events, this decorator cannot be chained with itself.

        To unregister the event callback, call its unregister_mpv_events function:

        ```
        player = mpv.MPV()
        @player.event_callback('shutdown')
        def my_handler(event):
            print('It ded.')

        my_handler.unregister_mpv_events()
        """

        def register(callback):
            types = [MpvEventID.from_str(t) if isinstance(t, str) else t for t in event_types] or MpvEventID.ANY

            @wraps(callback)
            def wrapper(event, *args, **kwargs):
                if event['event_id'] in types:
                    callback(event, *args, **kwargs)

            self._event_callbacks.append(wrapper)
            wrapper.unregister_mpv_events = partial(self.unregister_event_callback, wrapper)
            return wrapper

        return register

    @staticmethod
    def _binding_name(callback_or_cmd):
        return 'py_kb_{:016x}'.format(hash(callback_or_cmd) & 0xffffffffffffffff)

    def key_binding(self, keydef, mode='force'):
        """ Function decorator to register a key binding.

        The callback function signature is ```fun(key_state, key_name)``` where ```key_state``` is either ```'U'``` for
        "key up" or ```'D'``` for "key down".

        The keydef format is: ```[Shift+][Ctrl+][Alt+][Meta+]<key>``` where ```<key>``` is either the literal character
        the key produces (ASCII or Unicode character), or a symbolic name (as printed by ```mpv --input-keylist```)

        To unregister the callback function, you can call its ```unregister_mpv_key_bindings``` attribute:

        ```
        player = mpv.MPV()
        @player.key_binding('Q')
        def binding(state, name):
            print('blep')

        binding.unregister_mpv_key_bindings()
        ```

        WARNING: For a single keydef only a single callback/command can be registered at the same time. If you register
        a binding multiple times older bindings will be overwritten and there is a possibility of references leaking. So
        don't do that.

        BIG FAT WARNING: mpv's key binding mechanism is pretty powerful. This means, you essentially get arbitrary
        code exectution through key bindings. This interface makes some limited effort to sanitize the keydef given in
        the first parameter, but YOU SHOULD NOT RELY ON THIS IN FOR SECURITY. If your input comes from config files,
        this is completely fine--but, if you are about to pass untrusted input into this parameter, better double-check
        whether this is secure in your case. """

        def wrapper(fun):
            self.register_key_binding(keydef, fun, mode)
            return fun

        return wrapper

    def register_key_binding(self, keydef, callback_or_cmd, mode='force'):
        """ Register a key binding. This takes an mpv keydef and either a string containing a mpv
        command or a python callback function. See ```MPV.key_binding``` for details. """
        if not re.match(r'(Shift+)?(Ctrl+)?(Alt+)?(Meta+)?(.|\w+)', keydef):
            raise ValueError('Invalid keydef. Expected format: [Shift+][Ctrl+][Alt+][Meta+]<key>\n'
                             '<key> is either the literal character the key produces (ASCII or Unicode character), or a '
                             'symbolic name (as printed by --input-keylist')
        binding_name = MPV._binding_name(keydef)
        if callable(callback_or_cmd):
            callback_or_cmd.mpv_key_bindings = getattr(callback_or_cmd, 'mpv_key_bindings', []) + [keydef]

            def unregister_all():
                for keydef in callback_or_cmd.mpv_key_bindings:
                    self.unregister_key_binding(keydef)

            callback_or_cmd.unregister_mpv_key_bindings = unregister_all
            self._key_binding_handlers[binding_name] = callback_or_cmd
            self.register_message_handler('key-binding', self._handle_key_binding_message)
            self.command('define-section',
                         binding_name, '{} script-binding py_event_handler/{}'.format(keydef, binding_name), mode)
        elif isinstance(callback_or_cmd, str):
            self.command('define-section', binding_name, '{} {}'.format(keydef, callback_or_cmd), mode)
        else:
            raise TypeError('register_key_binding expects either an str with an mpv command or a python callable.')
        self.command('enable-section', binding_name)

    def _handle_key_binding_message(self, binding_name, key_state, key_name):
        self._key_binding_handlers[binding_name](key_state, key_name)

    def unregister_key_binding(self, keydef):
        """ Unregister a key binding by keydef """
        binding_name = MPV._binding_name(keydef)
        self.command('disable-section', binding_name)
        self.command('define-section', binding_name, '')
        if binding_name in self._key_binding_handlers:
            del self._key_binding_handlers[binding_name]
            if not self._key_binding_handlers:
                self.unregister_message_handler('key-binding')

    # Convenience functions
    def play(self, filename):
        """ Play a path or URL (requires ```ytdl``` option to be set) """
        self.loadfile(filename)

    @property
    def playlist_filenames(self):
        """ Return all playlist item file names/URLs as a list of strs """
        return [element['filename'] for element in self.playlist]

    def playlist_append(self, filename, **options):
        """ Append a path or URL to the playlist. This does not start playing the file automatically. To do that, use
        ```MPV.loadfile(filename, 'append-play')```. """
        self.loadfile(filename, 'append', **options)

    # Property accessors
    def _get_property(self, name, proptype=str, decode_str=False, force_format=None):
        fmt = force_format or {int: MpvFormat.INT64,
                               float: MpvFormat.DOUBLE,
                               bool: MpvFormat.FLAG,
                               str: MpvFormat.STRING,
                               bytes: MpvFormat.STRING,
                               _commalist: MpvFormat.STRING,
                               MpvFormat.NODE: MpvFormat.NODE}[proptype]

        out = cast(create_string_buffer(sizeof(c_void_p)), c_void_p)
        outptr = byref(out)
        try:
            cval = _mpv_get_property(self.handle, name.encode('utf-8'), fmt, outptr)
            rv = MpvNode.node_cast_value(outptr, fmt, decode_str or proptype in (str, _commalist))

            if proptype is _commalist:
                rv = proptype(rv)

            if proptype is str:
                _mpv_free(out)
            elif proptype is MpvFormat.NODE:
                _mpv_free_node_contents(outptr)

            return rv
        except PropertyUnavailableError as ex:
            return None

    def _set_property(self, name, value, proptype=str):
        ename = name.encode('utf-8')
        if type(value) is bytes:
            _mpv_set_property_string(self.handle, ename, value)
        elif type(value) is bool:
            _mpv_set_property_string(self.handle, ename, b'yes' if value else b'no')
        elif proptype in (str, int, float):
            _mpv_set_property_string(self.handle, ename, str(proptype(value)).encode('utf-8'))
        else:
            raise TypeError('Cannot set {} property {} to value of type {}'.format(proptype, name, type(value)))

    # Dict-like option access
    def __getitem__(self, name, file_local=False):
        """ Get an option value """
        prefix = 'file-local-options/' if file_local else 'options/'
        return self._get_property(prefix + name)

    def __setitem__(self, name, value, file_local=False):
        """ Set an option value """
        prefix = 'file-local-options/' if file_local else 'options/'
        return self._set_property(prefix + name, value)

    def __iter__(self):
        """ Iterate over all option names """
        return iter(self.options)

    def option_info(self, name):
        """ Get information on the given option """
        return self._get_property('option-info/' + name)


def _commalist(propval=''):
    return str(propval).split(',')


_node = MpvFormat.NODE

ALL_PROPERTIES = {
    'osd-level': (int, 'rw'),
    'osd-scale': (float, 'rw'),
    'loop': (str, 'rw'),
    'loop-file': (str, 'rw'),
    'speed': (float, 'rw'),
    'filename': (bytes, 'r'),
    'file-size': (int, 'r'),
    'path': (bytes, 'r'),
    'media-title': (bytes, 'r'),
    'stream-pos': (int, 'rw'),
    'stream-end': (int, 'r'),
    'length': (float, 'r'),  # deprecated for ages now
    'duration': (float, 'r'),
    'avsync': (float, 'r'),
    'total-avsync-change': (float, 'r'),
    #        'drop-frame-count':             (int,    'r'),
    'decoder-frame-drop-count': (int, 'r'),
    'percent-pos': (float, 'rw'),
    #        'ratio-pos':                    (float,  'rw'),
    'audio-pts': (float, 'r'),
    'time-pos': (float, 'rw'),
    'time-start': (float, 'r'),
    'time-remaining': (float, 'r'),
    'playtime-remaining': (float, 'r'),
    'chapter': (int, 'rw'),
    'edition': (str, 'rw'),
    'disc-titles': (int, 'r'),
    'disc-title': (str, 'rw'),
    #        'disc-menu-active':             (bool,   'r'),
    'chapters': (int, 'r'),
    'editions': (int, 'r'),
    'angle': (int, 'rw'),
    'pause': (bool, 'rw'),
    'core-idle': (bool, 'r'),
    'cache': (str, 'r'),
    'cache-size': (int, 'rw'),
    'cache-free': (int, 'r'),
    'cache-used': (int, 'r'),
    'cache-speed': (int, 'r'),
    'cache-idle': (bool, 'r'),
    'cache-buffering-state': (int, 'r'),
    'paused-for-cache': (bool, 'r'),
    #        'pause-for-cache':              (bool,   'r'),
    'eof-reached': (bool, 'r'),
    #        'pts-association-mode':         (str,    'rw'),
    'hr-seek': (str, 'rw'),
    'keepaspect': (bool, 'rw'),
    'volume': (float, 'rw'),
    'volume-max': (int, 'rw'),
    'ao-volume': (float, 'rw'),
    'mute': (bool, 'rw'),
    'ao-mute': (bool, 'rw'),
    'audio-speed-correction': (float, 'r'),
    'audio-delay': (float, 'rw'),
    'audio-format': (str, 'r'),
    'audio-codec': (str, 'r'),
    'audio-codec-name': (str, 'r'),
    'audio-bitrate': (float, 'r'),
    'packet-audio-bitrate': (float, 'r'),
    'audio-samplerate': (int, 'r'),
    'audio-channels': (str, 'r'),
    'aid': (str, 'rw'),
    'audio': (str, 'rw'),  # alias for aid
    'balance': (int, 'rw'),
    'fullscreen': (bool, 'rw'),
    'deinterlace': (str, 'rw'),
    'colormatrix': (str, 'rw'),
    'colormatrix-input-range': (str, 'rw'),
    #        'colormatrix-output-range':     (str,    'rw'),
    'colormatrix-primaries': (str, 'rw'),
    'ontop': (bool, 'rw'),
    'border': (bool, 'rw'),
    'framedrop': (str, 'rw'),
    'gamma': (float, 'rw'),
    'brightness': (int, 'rw'),
    'contrast': (int, 'rw'),
    'saturation': (int, 'rw'),
    'hue': (int, 'rw'),
    'hwdec': (str, 'rw'),
    'panscan': (float, 'rw'),
    'video-format': (str, 'r'),
    'video-codec': (str, 'r'),
    'video-bitrate': (float, 'r'),
    'packet-video-bitrate': (float, 'r'),
    'width': (int, 'r'),
    'height': (int, 'r'),
    'dwidth': (int, 'r'),
    'dheight': (int, 'r'),
    'container-fps': (float, 'r'),
    'estimated-vf-fps': (float, 'r'),
    'window-scale': (float, 'rw'),
    'video-aspect': (str, 'rw'),
    'osd-width': (int, 'r'),
    'osd-height': (int, 'r'),
    'osd-par': (float, 'r'),
    'vid': (str, 'rw'),
    'video': (str, 'rw'),  # alias for vid
    'video-align-x': (float, 'rw'),
    'video-align-y': (float, 'rw'),
    'video-pan-x': (float, 'rw'),
    'video-pan-y': (float, 'rw'),
    'video-zoom': (float, 'rw'),
    'video-unscaled': (bool, 'w'),
    'video-speed-correction': (float, 'r'),
    'program': (int, 'w'),
    'sid': (str, 'rw'),
    'sub': (str, 'rw'),  # alias for sid
    'secondary-sid': (str, 'rw'),
    'sub-delay': (float, 'rw'),
    'sub-pos': (int, 'rw'),
    'sub-visibility': (bool, 'rw'),
    'sub-forced-only': (bool, 'rw'),
    'sub-scale': (float, 'rw'),
    'sub-bitrate': (float, 'r'),
    'sub-text': (str, 'r'),
    'packet-sub-bitrate': (float, 'r'),
    #        'ass-use-margins':              (bool,   'rw'),
    'ass-vsfilter-aspect-compat': (bool, 'rw'),
    'ass-style-override': (str, 'rw'),
    #        'stream-capture':               (str,    'rw'),
    'tv-brightness': (int, 'rw'),
    'tv-contrast': (int, 'rw'),
    'tv-saturation': (int, 'rw'),
    'tv-hue': (int, 'rw'),
    'playlist-pos': (int, 'rw'),
    'playlist-pos-1': (int, 'rw'),  # ugh.
    'playlist-count': (int, 'r'),
    #        'quvi-format':                  (str,    'rw'),
    'seekable': (bool, 'r'),
    'seeking': (bool, 'r'),
    'partially-seekable': (bool, 'r'),
    'playback-abort': (bool, 'r'),
    'cursor-autohide': (str, 'rw'),
    'audio-device': (str, 'rw'),
    'current-vo': (str, 'r'),
    'current-ao': (str, 'r'),
    'audio-out-detected-device': (str, 'r'),
    'protocol-list': (str, 'r'),
    'mpv-version': (str, 'r'),
    'mpv-configuration': (str, 'r'),
    'ffmpeg-version': (str, 'r'),
    'display-sync-active': (bool, 'r'),
    'stream-open-filename': (bytes, 'rw'),  # Undocumented
    'file-format': (_commalist, 'r'),  # Be careful with this one.
    'mistimed-frame-count': (int, 'r'),
    'vsync-ratio': (float, 'r'),
    #        'vo-drop-frame-count':          (int,    'r'),
    'frame-drop-count': (int, 'r'),
    'vo-delayed-frame-count': (int, 'r'),
    'playback-time': (float, 'rw'),
    'demuxer-cache-duration': (float, 'r'),
    'demuxer-cache-time': (float, 'r'),
    'demuxer-cache-idle': (bool, 'r'),
    'demuxer-start-time': (float, 'r'),
    'demuxer-via-network': (bool, 'r'),
    #        'idle':                         (bool,   'r'),
    'idle-active': (bool, 'r'),  # dat name
    'disc-title-list': (_commalist, 'r'),
    'field-dominance': (str, 'rw'),
    'taskbar-progress': (bool, 'rw'),
    'on-all-workspaces': (bool, 'rw'),
    'video-output-levels': (str, 'r'),
    'vo-configured': (bool, 'r'),
    'hwdec-current': (str, 'r'),
    'hwdec-interop': (str, 'r'),
    'estimated-frame-count': (int, 'r'),
    'estimated-frame-number': (int, 'r'),
    'sub-use-margins': (bool, 'rw'),
    'ass-force-margins': (bool, 'rw'),
    'video-rotate': (str, 'rw'),
    'video-stereo-mode': (str, 'rw'),
    'ab-loop-a': (str, 'r'),  # What a mess...
    'ab-loop-b': (str, 'r'),
    'dvb-channel': (str, 'w'),
    'dvb-channel-name': (str, 'rw'),
    'window-minimized': (bool, 'r'),
    'display-names': (_commalist, 'r'),
    'display-fps': (float, 'r'),  # access apparently misdocumented in the manpage
    'estimated-display-fps': (float, 'r'),
    'vsync-jitter': (float, 'r'),
    'profile-list': (_node, 'r', False),
    'video-params': (_node, 'r', True),
    'video-dec-params': (_node, 'r', True),
    'video-out-params': (_node, 'r', True),
    'track-list': (_node, 'r', False),
    'playlist': (_node, 'r', False),
    'chapter-list': (_node, 'r', False),
    'vo-performance': (_node, 'r', True),
    'filtered-metadata': (_node, 'r', False),
    'metadata': (_node, 'r', False),
    'chapter-metadata': (_node, 'r', False),
    'vf-metadata': (_node, 'r', False),
    'af-metadata': (_node, 'r', False),
    'edition-list': (_node, 'r', False),
    'disc-titles': (_node, 'r', False),
    'audio-params': (_node, 'r', True),
    'audio-out-params': (_node, 'r', True),
    'audio-device-list': (_node, 'r', True),
    'video-frame-info': (_node, 'r', True),
    'decoder-list': (_node, 'r', True),
    'encoder-list': (_node, 'r', True),
    'vf': (_node, 'r', True),
    'af': (_node, 'r', True),
    'options': (_node, 'r', True),
    'file-local-options': (_node, 'r', True),
    'property-list': (_commalist, 'r')}


def _bindproperty(MPV, name, proptype, access, decode_str=False):
    getter = lambda self: self._get_property(name, proptype, decode_str)
    osdgetter = lambda osdself: osdself.mpv._get_property(name, force_format=MpvFormat.OSD_STRING)
    setter = lambda self, value: self._set_property(name, value, proptype)

    def barf(*args):
        raise NotImplementedError('Access denied')

    setattr(MPV, name.replace('-', '_'), property(getter if 'r' in access else barf, setter if 'w' in access else barf))
    setattr(OSDPropertyProxy, name.replace('-', '_'), property(osdgetter if 'r' in access else barf, barf))


for name, (proptype, access, *args) in ALL_PROPERTIES.items():
    _bindproperty(MPV, name, proptype, access, *args)
