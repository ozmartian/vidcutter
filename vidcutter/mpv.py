#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import ctypes.util
import os
import re
import sys
import threading
import traceback
from ctypes import *
from functools import partial

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
    if sofile is None:
        sofile = 'libmpv.so.1'

    try:
        backend = CDLL(sofile)
    except OSError:
        raise OSError("Cannot find libmpv in the usual places.")

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

    def as_dict(self):
        if self.format.value == MpvFormat.STRING:
            proptype, _access = ALL_PROPERTIES.get(self.name, (str, None))
            return {'name': self.name.decode('utf-8'),
                    'format': self.format,
                    'data': self.data,
                    'value': proptype(cast(self.data, POINTER(c_char_p)).contents.value.decode('utf-8'))}
        else:
            return {'name': self.name.decode('utf-8'),
                    'format': self.format,
                    'data': self.data}


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
                name = pc['name']

                if 'value' in pc:
                    proptype, _access = ALL_PROPERTIES[name]
                    if proptype is bytes:
                        args = (pc['value'],)
                    else:
                        args = (proptype(_ensure_encoding(pc['value'])),)
                elif pc['format'] == MpvFormat.NONE:
                    args = (None,)
                else:
                    args = (pc['data'], pc['format'])

                for handler in property_handlers[name]:
                    handler(*args)
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


class MPV(object):
    """ See man mpv(1) for the details of the implemented commands. """

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

        self._event_callbacks = []
        self._property_handlers = collections.defaultdict(lambda: [])
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
        sema = threading.Semaphore(value=0)

        def observer(val):
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
        _mpv_request_log_messages(self._event_handle, level.encode('utf-8'))

    def command(self, name, *args):
        """ Execute a raw command """
        args = [name.encode('utf-8')] + [(arg if type(arg) is bytes else str(arg).encode('utf-8'))
                                         for arg in args if arg is not None] + [None]
        _mpv_command(self.handle, (c_char_p * len(args))(*args))

    def seek(self, amount, reference="relative", precision="default-precise"):
        self.command('seek', amount, reference, precision)

    def revert_seek(self):
        self.command('revert_seek');

    def frame_step(self):
        self.command('frame_step')

    def frame_back_step(self):
        self.command('frame_back_step')

    def _add_property(self, name, value=None):
        self.command('add_property', name, value)

    def _cycle_property(self, name, direction='up'):
        self.command('cycle_property', name, direction)

    def _multiply_property(self, name, factor):
        self.command('multiply_property', name, factor)

    def screenshot(self, includes='subtitles', mode='single'):
        self.command('screenshot', includes, mode)

    def screenshot_to_file(self, filename, includes='subtitles'):
        self.command('screenshot_to_file', filename.encode(fs_enc), includes)

    def playlist_next(self, mode='weak'):
        self.command('playlist_next', mode)

    def playlist_prev(self, mode='weak'):
        self.command('playlist_prev', mode)

    @staticmethod
    def _encode_options(options):
        return ','.join('{}={}'.format(str(key), str(val)) for key, val in options.items())

    def loadfile(self, filename, mode='replace', **options):
        self.command('loadfile', filename.encode(fs_enc), mode, MPV._encode_options(options))

    def loadlist(self, playlist, mode='replace'):
        self.command('loadlist', playlist.encode(fs_enc), mode)

    def playlist_clear(self):
        self.command('playlist_clear')

    def playlist_remove(self, index='current'):
        self.command('playlist_remove', index)

    def playlist_move(self, index1, index2):
        self.command('playlist_move', index1, index2)

    def run(self, command, *args):
        self.command('run', command, *args)

    def quit(self, code=None):
        self.command('quit', code)

    def quit_watch_later(self, code=None):
        self.command('quit_watch_later', code)

    def sub_add(self, filename):
        self.command('sub_add', filename.encode(fs_enc))

    def sub_remove(self, sub_id=None):
        self.command('sub_remove', sub_id)

    def sub_reload(self, sub_id=None):
        self.command('sub_reload', sub_id)

    def sub_step(self, skip):
        self.command('sub_step', skip)

    def sub_seek(self, skip):
        self.command('sub_seek', skip)

    def toggle_osd(self):
        self.command('osd')

    def show_text(self, string, duration='-', level=None):
        self.command('show_text', string, duration, level)

    def show_progress(self):
        self.command('show_progress')

    def discnav(self, command):
        self.command('discnav', command)

    def write_watch_later_config(self):
        self.command('write_watch_later_config')

    def overlay_add(self, overlay_id, x, y, file_or_fd, offset, fmt, w, h, stride):
        self.command('overlay_add', overlay_id, x, y, file_or_fd, offset, fmt, w, h, stride)

    def overlay_remove(self, overlay_id):
        self.command('overlay_remove', overlay_id)

    def script_message(self, *args):
        self.command('script_message', *args)

    def script_message_to(self, target, *args):
        self.command('script_message_to', target, *args)

    def observe_property(self, name, handler):
        self._property_handlers[name].append(handler)
        _mpv_observe_property(self._event_handle, hash(name) & 0xffffffffffffffff, name.encode('utf-8'),
                              MpvFormat.STRING)

    def unobserve_property(self, name, handler):
        handlers = self._property_handlers[name]
        handlers.remove(handler)
        if not handlers:
            _mpv_unobserve_property(self._event_handle, hash(name) & 0xffffffffffffffff)

    def register_message_handler(self, target, handler):
        self._message_handlers[target] = handler

    def unregister_message_handler(self, target):
        del self._message_handlers[target]

    def register_event_callback(self, callback):
        self._event_callbacks.append(callback)

    def unregister_event_callback(self, callback):
        self._event_callbacks.remove(callback)

    @staticmethod
    def _binding_name(callback_or_cmd):
        return 'py_kb_{:016x}'.format(hash(callback_or_cmd) & 0xffffffffffffffff)

    def register_key_binding(self, keydef, callback_or_cmd, mode='force'):
        """ BIG FAT WARNING: mpv's key binding mechanism is pretty powerful. This means, you essentially get arbitrary
        code exectution through key bindings. This interface makes some limited effort to sanitize the keydef given in
        the first parameter, but YOU SHOULD NOT RELY ON THIS IN FOR SECURITY. If your input comes from config files,
        this is completely fine--but, if you are about to pass untrusted input into this parameter, better double-check
        whether this is secure in your case. """
        if not re.match(r'(Shift+)?(Ctrl+)?(Alt+)?(Meta+)?(.|\w+)', keydef):
            raise ValueError('Invalid keydef. Expected format: [Shift+][Ctrl+][Alt+][Meta+]<key>\n'
                             '<key> is either the literal character the key produces (ASCII or Unicode character), or a '
                             'symbolic name (as printed by --input-keylist')
        binding_name = MPV._binding_name(keydef)
        if callable(callback_or_cmd):
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
        binding_name = MPV._binding_name(keydef)
        self.command('disable-section', binding_name)
        self.command('define-section', binding_name, '')
        if callable(callback):
            del self._key_binding_handlers[binding_name]
            if not self._key_binding_handlers:
                self.unregister_message_handler('key-binding')

    # Convenience functions
    def play(self, filename):
        self.loadfile(filename)

    # Property accessors
    def _get_property(self, name, proptype=str, decode_str=False):
        fmt = {int: MpvFormat.INT64,
               float: MpvFormat.DOUBLE,
               bool: MpvFormat.FLAG,
               str: MpvFormat.STRING,
               bytes: MpvFormat.STRING,
               commalist: MpvFormat.STRING,
               MpvFormat.NODE: MpvFormat.NODE}[proptype]

        out = cast(create_string_buffer(sizeof(c_void_p)), c_void_p)
        outptr = byref(out)
        try:
            cval = _mpv_get_property(self.handle, name.encode('utf-8'), fmt, outptr)
            rv = MpvNode.node_cast_value(outptr, fmt, decode_str or proptype in (str, commalist))

            if proptype is commalist:
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
        """ Get an option value """
        prefix = 'file-local-options/' if file_local else 'options/'
        return self._set_property(prefix + name, value)

    def __iter__(self):
        return iter(self.options)

    def option_info(self, name):
        return self._get_property('option-info/' + name)


def commalist(propval=''):
    return str(propval).split(',')


node = MpvFormat.NODE

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
    'drop-frame-count': (int, 'r'),
    'percent-pos': (float, 'rw'),
    #        'ratio-pos':                    (float,  'rw'),
    'time-pos': (float, 'rw'),
    'time-start': (float, 'r'),
    'time-remaining': (float, 'r'),
    'playtime-remaining': (float, 'r'),
    'chapter': (int, 'rw'),
    'edition': (int, 'rw'),
    'disc-titles': (int, 'r'),
    'disc-title': (str, 'rw'),
    #        'disc-menu-active':             (bool,   'r'),
    'chapters': (int, 'r'),
    'editions': (int, 'r'),
    'angle': (int, 'rw'),
    'pause': (bool, 'rw'),
    'core-idle': (bool, 'r'),
    'cache': (int, 'r'),
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
    'fps': (float, 'r'),
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
    'packet-sub-bitrate': (float, 'r'),
    #        'ass-use-margins':              (bool,   'rw'),
    'ass-vsfilter-aspect-compat': (bool, 'rw'),
    'ass-style-override': (bool, 'rw'),
    'stream-capture': (str, 'rw'),
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
    'file-format': (commalist, 'r'),  # Be careful with this one.
    'mistimed-frame-count': (int, 'r'),
    'vsync-ratio': (float, 'r'),
    'vo-drop-frame-count': (int, 'r'),
    'vo-delayed-frame-count': (int, 'r'),
    'playback-time': (float, 'rw'),
    'demuxer-cache-duration': (float, 'r'),
    'demuxer-cache-time': (float, 'r'),
    'demuxer-cache-idle': (bool, 'r'),
    'idle': (bool, 'r'),
    'disc-title-list': (commalist, 'r'),
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
    'display-names': (commalist, 'r'),
    'display-fps': (float, 'r'),  # access apparently misdocumented in the manpage
    'estimated-display-fps': (float, 'r'),
    'vsync-jitter': (float, 'r'),
    'video-params': (node, 'r', True),
    'video-out-params': (node, 'r', True),
    'track-list': (node, 'r', False),
    'playlist': (node, 'r', False),
    'chapter-list': (node, 'r', False),
    'vo-performance': (node, 'r', True),
    'filtered-metadata': (node, 'r', False),
    'metadata': (node, 'r', False),
    'chapter-metadata': (node, 'r', False),
    'vf-metadata': (node, 'r', False),
    'af-metadata': (node, 'r', False),
    'edition-list': (node, 'r', False),
    'audio-params': (node, 'r', True),
    'audio-out-params': (node, 'r', True),
    'audio-device-list': (node, 'r', True),
    'video-frame-info': (node, 'r', True),
    'decoder-list': (node, 'r', True),
    'encoder-list': (node, 'r', True),
    'vf': (node, 'r', True),
    'af': (node, 'r', True),
    'options': (node, 'r', True),
    'file-local-options': (node, 'r', True),
    'property-list': (commalist, 'r')}


def bindproperty(MPV, name, proptype, access, decode_str=False):
    getter = lambda self: self._get_property(name, proptype, decode_str)
    setter = lambda self, value: self._set_property(name, value, proptype)

    def barf(*args):
        raise NotImplementedError('Access denied')

    setattr(MPV, name.replace('-', '_'), property(getter if 'r' in access else barf, setter if 'w' in access else barf))


for name, (proptype, access, *args) in ALL_PROPERTIES.items():
    bindproperty(MPV, name, proptype, access, *args)
