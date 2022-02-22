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

"""pympv - Python wrapper for libmpv

libmpv is a client library for the media player mpv

For more info see: https://github.com/mpv-player/mpv/blob/master/libmpv/client.h
"""

import cython
import sys, warnings
from threading import Thread, Semaphore
from libc.stdlib cimport malloc, free
from libc.string cimport strcpy, strlen, memset
from cpython.pycapsule cimport PyCapsule_IsValid, PyCapsule_GetPointer

from client cimport *

__version__ = "0.3.0"
__author__ = "Andre D"

_REQUIRED_CAPI_MAJOR = 2
_MIN_CAPI_MINOR = 0

cdef unsigned long _CAPI_VERSION
with nogil:
    _CAPI_VERSION = mpv_client_api_version()

_CAPI_MAJOR = _CAPI_VERSION >> 16
_CAPI_MINOR = _CAPI_VERSION & 0xFFFF

if _CAPI_MAJOR != _REQUIRED_CAPI_MAJOR or _CAPI_MINOR < _MIN_CAPI_MINOR:
    raise ImportError(
        "libmpv version is incorrect. Required %d.%d got %d.%d." %
            (_REQUIRED_CAPI_MAJOR, _MIN_CAPI_MINOR, _CAPI_MAJOR, _CAPI_MINOR)
    )

cdef extern from "Python.h":
    void Py_Initialize()

_is_py3 = sys.version_info >= (3,)
_strdec_err = "surrogateescape" if _is_py3 else "strict"
# mpv -> Python
def _strdec(s):
    try:
        return s.decode("utf-8", _strdec_err)
    except UnicodeDecodeError:
        # In python2, bail to bytes on failure
        return bytes(s)

# Python -> mpv
def _strenc(s):
    try:
        return s.encode("utf-8", _strdec_err)
    except UnicodeEncodeError:
        # In python2, assume bytes and walk right through
        return s

Py_Initialize()

class Errors:
    """Set of known error codes from MpvError and Event responses.

    Mostly wraps the enum mpv_error.
    Values might not always be integers in the future.
    You should handle the possibility that error codes may not be any of these values.
    """
    success = MPV_ERROR_SUCCESS
    queue_full = MPV_ERROR_EVENT_QUEUE_FULL
    nomem = MPV_ERROR_NOMEM
    uninitialized = MPV_ERROR_UNINITIALIZED
    invalid_parameter = MPV_ERROR_INVALID_PARAMETER
    not_found = MPV_ERROR_OPTION_NOT_FOUND
    option_format = MPV_ERROR_OPTION_FORMAT
    option_error = MPV_ERROR_OPTION_ERROR
    not_found = MPV_ERROR_PROPERTY_NOT_FOUND
    property_format = MPV_ERROR_PROPERTY_FORMAT
    property_unavailable = MPV_ERROR_PROPERTY_UNAVAILABLE
    property_error = MPV_ERROR_PROPERTY_ERROR
    command_error = MPV_ERROR_COMMAND
    loading_failed = MPV_ERROR_LOADING_FAILED
    ao_init_failed = MPV_ERROR_AO_INIT_FAILED
    vo_init_failed = MPV_ERROR_VO_INIT_FAILED
    nothing_to_play = MPV_ERROR_NOTHING_TO_PLAY
    unknown_format = MPV_ERROR_UNKNOWN_FORMAT
    unsupported = MPV_ERROR_UNSUPPORTED
    not_implemented = MPV_ERROR_NOT_IMPLEMENTED


class Events:
    """Set of known values for Event ids.

    Mostly wraps the enum mpv_event_id.
    Values might not always be integers in the future.
    You should handle the possibility that event ids may not be any of these values.
    """
    none = MPV_EVENT_NONE
    shutdown = MPV_EVENT_SHUTDOWN
    log_message = MPV_EVENT_LOG_MESSAGE
    get_property_reply = MPV_EVENT_GET_PROPERTY_REPLY
    set_property_reply = MPV_EVENT_SET_PROPERTY_REPLY
    command_reply = MPV_EVENT_COMMAND_REPLY
    start_file = MPV_EVENT_START_FILE
    end_file = MPV_EVENT_END_FILE
    file_loaded = MPV_EVENT_FILE_LOADED
    # tracks_changed = MPV_EVENT_TRACKS_CHANGED
    # tracks_switched = MPV_EVENT_TRACK_SWITCHED
    idle = MPV_EVENT_IDLE
    # pause = MPV_EVENT_PAUSE
    # unpause = MPV_EVENT_UNPAUSE
    tick = MPV_EVENT_TICK
    # script_input_dispatch = MPV_EVENT_SCRIPT_INPUT_DISPATCH
    client_message = MPV_EVENT_CLIENT_MESSAGE
    video_reconfig = MPV_EVENT_VIDEO_RECONFIG
    audio_reconfig = MPV_EVENT_AUDIO_RECONFIG
    # metadata_update = MPV_EVENT_METADATA_UPDATE
    seek = MPV_EVENT_SEEK
    playback_restart = MPV_EVENT_PLAYBACK_RESTART
    property_change = MPV_EVENT_PROPERTY_CHANGE
    # chapter_change = MPV_EVENT_CHAPTER_CHANGE


class LogLevels:
    no = MPV_LOG_LEVEL_NONE
    fatal = MPV_LOG_LEVEL_FATAL
    error = MPV_LOG_LEVEL_ERROR
    warn = MPV_LOG_LEVEL_WARN
    info = MPV_LOG_LEVEL_INFO
    v = MPV_LOG_LEVEL_V
    debug = MPV_LOG_LEVEL_DEBUG
    trace = MPV_LOG_LEVEL_TRACE


class EOFReasons:
    """Known possible values for EndOfFileReached reason.

    You should handle the possibility that the reason may not be any of these values.
    """
    eof = MPV_END_FILE_REASON_EOF
    aborted = MPV_END_FILE_REASON_STOP
    quit = MPV_END_FILE_REASON_QUIT
    error = MPV_END_FILE_REASON_ERROR


cdef class EndOfFileReached(object):
    """Data field for MPV_EVENT_END_FILE events

    Wraps: mpv_event_end_file
    """
    cdef public object reason, error

    cdef _init(self, mpv_event_end_file* eof):
        self.reason = eof.reason
        self.error = eof.error
        return self


# cdef class InputDispatch(object):
#     """Data field for MPV_EVENT_SCRIPT_INPUT_DISPATCH events.

#     Wraps: mpv_event_script_input_dispatch
#     """
#     cdef public object arg0, type

#     cdef _init(self, mpv_event_script_input_dispatch* input):
#         self.arg0 = input.arg0
#         self.type = _strdec(input.type)
#         return self


cdef class LogMessage(object):
    """Data field for MPV_EVENT_LOG_MESSAGE events.

    Wraps: mpv_event_log_message
    """
    cdef public object prefix, level, text, log_level

    cdef _init(self, mpv_event_log_message* msg):
        self.level = _strdec(msg.level)
        self.prefix = _strdec(msg.prefix)
        self.text = _strdec(msg.text)
        self.log_level = msg.log_level
        return self


cdef _convert_node_value(mpv_node node):
    if node.format == MPV_FORMAT_STRING:
        return _strdec(node.u.string)
    elif node.format == MPV_FORMAT_FLAG:
        return not not int(node.u.flag)
    elif node.format == MPV_FORMAT_INT64:
        return int(node.u.int64)
    elif node.format == MPV_FORMAT_DOUBLE:
        return float(node.u.double_)
    elif node.format == MPV_FORMAT_NODE_MAP:
        return _convert_value(node.u.list, node.format)
    elif node.format == MPV_FORMAT_NODE_ARRAY:
        return _convert_value(node.u.list, node.format)
    return None


cdef _convert_value(void* data, mpv_format format):
    cdef mpv_node node
    cdef mpv_node_list nodelist
    if format == MPV_FORMAT_NODE:
        node = (<mpv_node*>data)[0]
        return _convert_node_value(node)
    elif format == MPV_FORMAT_NODE_ARRAY:
        nodelist = (<mpv_node_list*>data)[0]
        values = []
        for i in range(nodelist.num):
            values.append(_convert_node_value(nodelist.values[i]))
        return values
    elif format == MPV_FORMAT_NODE_MAP:
        nodelist = (<mpv_node_list*>data)[0]
        values = {}
        for i in range(nodelist.num):
            value = _convert_node_value(nodelist.values[i])
            values[_strdec(nodelist.keys[i])] = value
        return values
    elif format == MPV_FORMAT_STRING:
        return _strdec(((<char**>data)[0]))
    elif format == MPV_FORMAT_FLAG:
        return not not (<uint64_t*>data)[0]
    elif format == MPV_FORMAT_INT64:
        return int((<uint64_t*>data)[0])
    elif format == MPV_FORMAT_DOUBLE:
        return float((<double*>data)[0])
    return None


cdef class Property(object):
    """Data field for MPV_EVENT_PROPERTY_CHANGE and MPV_EVENT_GET_PROPERTY_REPLY.

    Wraps: mpv_event_property
    """
    cdef public object name, data

    cdef _init(self, mpv_event_property* prop):
        self.name = _strdec(prop.name)
        self.data = _convert_value(prop.data, prop.format)
        return self


cdef class Event(object):
    """Wraps: mpv_event"""
    cdef public mpv_event_id id
    cdef public int error
    cdef public object data, reply_userdata

    @property
    def error_str(self):
        """mpv_error_string of the error proeprty"""
        cdef const char* err_c
        with nogil:
            err_c = mpv_error_string(self.error)
        return _strdec(err_c)

    cdef _data(self, mpv_event* event):
        cdef void* data = event.data
        cdef mpv_event_client_message* climsg
        if self.id == MPV_EVENT_GET_PROPERTY_REPLY:
            return Property()._init(<mpv_event_property*>data)
        elif self.id == MPV_EVENT_PROPERTY_CHANGE:
            return Property()._init(<mpv_event_property*>data)
        elif self.id == MPV_EVENT_LOG_MESSAGE:
            return LogMessage()._init(<mpv_event_log_message*>data)
        # elif self.id == MPV_EVENT_SCRIPT_INPUT_DISPATCH:
        #     return InputDispatch()._init(<mpv_event_script_input_dispatch*>data)
        elif self.id == MPV_EVENT_CLIENT_MESSAGE:
            climsg = <mpv_event_client_message*>data
            args = []
            num_args = climsg.num_args
            for i in range(num_args):
                arg = <char*>climsg.args[i]
                arg = _strdec(arg)
                args.append(arg)
            return args
        elif self.id == MPV_EVENT_END_FILE:
            return EndOfFileReached()._init(<mpv_event_end_file*>data)
        return None

    @property
    def name(self):
        """mpv_event_name of the event id"""
        cdef const char* name_c
        with nogil:
            name_c = mpv_event_name(self.id)
        return _strdec(name_c)

    cdef _init(self, mpv_event* event, ctx):
        cdef uint64_t ctxid = <uint64_t>id(ctx)
        self.id = event.event_id
        self.data = self._data(event)
        userdata = _reply_userdatas[ctxid].get(event.reply_userdata, None)
        if userdata is not None and self.id != MPV_EVENT_PROPERTY_CHANGE:
            userdata.remove()
            if not userdata.observed and userdata.counter <= 0:
                del _reply_userdatas[ctxid][event.reply_userdata]
        if userdata is not None:
            userdata = userdata.data
        self.reply_userdata = userdata
        self.error = event.error
        return self


def _errors(fn):
    def wrapped(*k, **kw):
        v = fn(*k, **kw)
        if v < 0:
            raise MPVError(v)
    return wrapped


class MPVError(Exception):
    code = None

    def __init__(self, e):
        self.code = e
        cdef const char* err_c
        cdef int e_i
        if not isinstance(e, basestring):
            e_i = e
            with nogil:
                err_c = mpv_error_string(e_i)
            e = _strdec(err_c)
        Exception.__init__(self, e)

class PyMPVError(Exception):
    pass

cdef _callbacks = dict()
cdef _reply_userdatas = dict()

class _ReplyUserData(object):
    def __init__(self, data):
        self.counter = 0
        self.data = data
        self.observed = False

    def add(self):
        self.counter += 1

    def remove(self):
        self.counter -= 1


cdef class Context(object):
    """Base class wrapping a context to interact with mpv.

    Assume all calls can raise MPVError.

    Wraps: mpv_create, mpv_destroy and all mpv_handle related calls
    """
    cdef mpv_handle *_ctx
    cdef object callback, callbackthread, reply_userdata

    @property
    def api_version(self):
        return _CAPI_MINOR, _CAPI_MAJOR, _CAPI_VERSION

    @property
    def name(self):
        """Unique name for every context created.

        Wraps: mpv_client_name
        """
        cdef const char* name
        assert self._ctx
        with nogil:
            name = mpv_client_name(self._ctx)
        return _strdec(name)

    @property
    def time(self):
        """Internal mpv client time.

        Has an arbitrary start offset, but will never wrap or go backwards.

        Wraps: mpv_get_time_us
        """
        cdef int64_t time
        assert self._ctx
        with nogil:
            time = mpv_get_time_us(self._ctx)
        return time

    # def suspend(self):
    #     """Wraps: mpv_suspend"""
    #     assert self._ctx
    #     with nogil:
    #         mpv_suspend(self._ctx)

    # def resume(self):
    #     """Wraps: mpv_resume"""
    #     assert self._ctx
    #     with nogil:
    #         mpv_resume(self._ctx)

    @_errors
    def request_event(self, event, enable):
        """Enable or disable a given event.

        Arguments:
        event - See Events
        enable - True to enable, False to disable

        Wraps: mpv_request_event
        """
        assert self._ctx
        cdef int enable_i = 1 if enable else 0
        cdef int err
        cdef mpv_event_id event_id = event
        with nogil:
            err = mpv_request_event(self._ctx, event_id, enable_i)
        return err

    @_errors
    def set_log_level(self, loglevel):
        """Wraps: mpv_request_log_messages"""
        assert self._ctx
        loglevel = _strenc(loglevel)
        cdef const char* loglevel_c = loglevel
        cdef int err
        with nogil:
            err = mpv_request_log_messages(self._ctx, loglevel_c)
        return err

    @_errors
    def load_config(self, filename):
        """Wraps: mpv_load_config_file"""
        assert self._ctx
        filename = _strenc(filename)
        cdef const char* _filename = filename
        cdef int err
        with nogil:
            err = mpv_load_config_file(self._ctx, _filename)
        return err

    def _format_for(self, value):
        if isinstance(value, basestring):
            return MPV_FORMAT_STRING
        elif isinstance(value, bool):
            return MPV_FORMAT_FLAG
        elif isinstance(value, int):
            return MPV_FORMAT_INT64
        elif isinstance(value, float):
            return MPV_FORMAT_DOUBLE
        elif isinstance(value, (tuple, list)):
            return MPV_FORMAT_NODE_ARRAY
        elif isinstance(value, dict):
            return MPV_FORMAT_NODE_MAP
        return MPV_FORMAT_NONE

    cdef mpv_node_list* _prep_node_list(self, values):
        cdef mpv_node node
        cdef mpv_format format
        cdef mpv_node_list* node_list = <mpv_node_list*>malloc(sizeof(mpv_node_list))
        node_list.num = len(values)
        node_list.values = NULL
        node_list.keys = NULL
        if node_list.num:
            node_list.values = <mpv_node*>malloc(node_list.num * sizeof(mpv_node))
        for i, value in enumerate(values):
            format = self._format_for(value)
            node = self._prep_native_value(value, format)
            node_list.values[i] = node
        return node_list

    cdef mpv_node_list* _prep_node_map(self, map):
        cdef char* ckey
        cdef mpv_node_list* list
        list = self._prep_node_list(map.values())
        keys = map.keys()
        if not len(keys):
            return list
        list.keys = <char**>malloc(list.num)
        for i, key in enumerate(keys):
            key = _strenc(key)
            ckey = key
            list.keys[i] = <char*>malloc(len(key) + 1)
            strcpy(list.keys[i], ckey)
        return list

    cdef mpv_node _prep_native_value(self, value, format):
        cdef mpv_node node
        node.format = format
        if format == MPV_FORMAT_STRING:
            value = _strenc(value)
            node.u.string = <char*>malloc(len(value) + 1)
            strcpy(node.u.string, value)
        elif format == MPV_FORMAT_FLAG:
            node.u.flag = 1 if value else 0
        elif format == MPV_FORMAT_INT64:
            node.u.int64 = value
        elif format == MPV_FORMAT_DOUBLE:
            node.u.double_ = value
        elif format == MPV_FORMAT_NODE_ARRAY:
            node.u.list = self._prep_node_list(value)
        elif format == MPV_FORMAT_NODE_MAP:
            node.u.list = self._prep_node_map(value)
        else:
            node.format = MPV_FORMAT_NONE
        return node

    cdef _free_native_value(self, mpv_node node):
        if node.format in (MPV_FORMAT_NODE_ARRAY, MPV_FORMAT_NODE_MAP):
            for i in range(node.u.list.num):
                self._free_native_value(node.u.list.values[i])
            free(node.u.list.values)
            if node.format == MPV_FORMAT_NODE_MAP:
                for i in range(node.u.list.num):
                    free(node.u.list.keys[i])
                free(node.u.list.keys)
            free(node.u.list)
        elif node.format == MPV_FORMAT_STRING:
            free(node.u.string)

    def command(self, *cmdlist, asynchronous=False, data=None):
        """Send a command to mpv.

        Non-async success returns the command's response data, otherwise None

        Arguments:
        Accepts parameters as args

        Keyword Arguments:
        asynchronous: True will return right away, status comes in as MPV_EVENT_COMMAND_REPLY
        data: Only valid if async, gets sent back as reply_userdata in the Event

        Wraps: mpv_command_node and mpv_command_node_async
        """
        assert self._ctx
        cdef mpv_node node = self._prep_native_value(cmdlist, self._format_for(cmdlist))
        cdef mpv_node noderesult
        cdef int err
        cdef uint64_t data_id
        result = None
        try:
            data_id = id(data)
            if not asynchronous:
                with nogil:
                    err = mpv_command_node(self._ctx, &node, &noderesult)
                try:
                    result = _convert_node_value(noderesult) if err >= 0 else None
                finally:
                    with nogil:
                        mpv_free_node_contents(&noderesult)
            else:
                userdatas = self.reply_userdata.get(data_id, None)
                if userdatas is None:
                    _reply_userdatas[data_id] = userdatas = _ReplyUserData(data)
                userdatas.add()
                with nogil:
                    err = mpv_command_node_async(self._ctx, data_id, &node)
        finally:
            self._free_native_value(node)
        if err < 0:
            raise MPVError(err)
        return result

    @_errors
    def get_property_async(self, prop, data=None):
        """Gets the value of a property asynchronously.

        Arguments:
        prop: Property to get the value of.

        Keyword arguments:
        data: Value to be passed into the reply_userdata of the response event.
        Wraps: mpv_get_property_async"""
        assert self._ctx
        prop = _strenc(prop)
        cdef uint64_t id_data = <uint64_t>hash(data)
        userdatas = self.reply_userdata.get(id_data, None)
        if userdatas is None:
            self.reply_userdata[id_data] = userdatas = _ReplyUserData(data)
        userdatas.add()
        cdef const char* prop_c = prop
        with nogil:
            err = mpv_get_property_async(
                self._ctx,
                id_data,
                prop_c,
                MPV_FORMAT_NODE,
            )
        return err

    def try_get_property_async(self, prop, data=None, default=None):
        try:
            return self.get_property_async(prop, data=data)
        except MPVError:
            return default

    def try_get_property(self, prop, default=None):
        try:
            return self.get_property(prop)
        except MPVError:
            return default

    def get_property(self, prop):
        """Wraps: mpv_get_property"""
        assert self._ctx
        cdef mpv_node result
        prop = _strenc(prop)
        cdef const char* prop_c = prop
        cdef int err
        with nogil:
            err = mpv_get_property(
                self._ctx,
                prop_c,
                MPV_FORMAT_NODE,
                &result,
            )
        if err < 0:
            raise MPVError(err)
        try:
            v = _convert_node_value(result)
        finally:
            with nogil:
                mpv_free_node_contents(&result)
        return v

    @_errors
    def set_property(self, prop, value=True, asynchronous=False, data=None):
        """Wraps: mpv_set_property and mpv_set_property_async"""
        assert self._ctx
        prop = _strenc(prop)
        cdef mpv_format format = self._format_for(value)
        cdef mpv_node v = self._prep_native_value(value, format)
        cdef int err
        cdef uint64_t data_id
        cdef const char* prop_c
        try:
            prop_c = prop
            if not asynchronous:
                with nogil:
                    err = mpv_set_property(
                        self._ctx,
                        prop_c,
                        MPV_FORMAT_NODE,
                        &v
                    )
                return err
            data_id = <uint64_t>hash(data)
            userdatas = self.reply_userdata.get(data_id, None)
            if userdatas is None:
                self.reply_userdata[data_id] = userdatas = _ReplyUserData(data)
            userdatas.add()
            with nogil:
                err = mpv_set_property_async(
                    self._ctx,
                    data_id,
                    prop_c,
                    MPV_FORMAT_NODE,
                    &v
                )
        finally:
            self._free_native_value(v)
        return err

    @_errors
    def set_option(self, prop, value=True):
        """Wraps: mpv_set_option"""
        assert self._ctx
        prop = _strenc(prop)
        cdef mpv_format format = self._format_for(value)
        cdef mpv_node v = self._prep_native_value(value, format)
        cdef int err
        cdef const char* prop_c
        try:
            prop_c = prop
            with nogil:
                err = mpv_set_option(
                    self._ctx,
                    prop_c,
                    MPV_FORMAT_NODE,
                    &v
                )
        finally:
            self._free_native_value(v)
        return err

    @_errors
    def initialize(self):
        """Wraps: mpv_initialize"""
        assert self._ctx
        cdef int err
        with nogil:
            err = mpv_initialize(self._ctx)
        return err

    def wait_event(self, timeout=None):
        """Wraps: mpv_wait_event"""
        assert self._ctx
        cdef double timeout_d = timeout if timeout is not None else -1
        cdef mpv_event* event
        with nogil:
            event = mpv_wait_event(self._ctx, timeout_d)
        return Event()._init(event, self)

    def wakeup(self):
        """Wraps: mpv_wakeup"""
        assert self._ctx
        with nogil:
            mpv_wakeup(self._ctx)

    def set_wakeup_callback(self, callback):
        """Wraps: mpv_set_wakeup_callback"""
        assert self._ctx
        cdef uint64_t name = <uint64_t>id(self)
        self.callback = callback
        self.callbackthread.set(callback)
        with nogil:
            mpv_set_wakeup_callback(self._ctx, _c_callback, <void*>name)

    def get_wakeup_pipe(self):
        """Wraps: mpv_get_wakeup_pipe"""
        assert self._ctx
        cdef int pipe
        with nogil:
            pipe = mpv_get_wakeup_pipe(self._ctx)
        return pipe

    def __cinit__(self):
        cdef uint64_t ctxid = <uint64_t>id(self)
        with nogil:
            self._ctx = mpv_create()
        if not self._ctx:
            raise MPVError("Context creation error")
        self.callbackthread = CallbackThread()
        _callbacks[ctxid] = self.callbackthread
        self.reply_userdata = dict()
        _reply_userdatas[ctxid] = self.reply_userdata
        self.callbackthread.start()

    @_errors
    def observe_property(self, prop, data=None):
        """Wraps: mpv_observe_property"""
        assert self._ctx
        cdef uint64_t id_data = <uint64_t>hash(data)
        id_data = <uint64_t>hash(data)
        userdatas = self.reply_userdata.get(id_data, None)
        if userdatas is None:
            self.reply_userdata[id_data] = userdatas = _ReplyUserData(data)
        userdatas.observed = True
        prop = _strenc(prop)
        cdef char* propc = prop
        cdef int err
        with nogil:
            err = mpv_observe_property(
                self._ctx,
                id_data,
                propc,
                MPV_FORMAT_NODE,
            )
        return err

    @_errors
    def unobserve_property(self, data):
        """Wraps: mpv_unobserve_property"""
        assert self._ctx
        cdef uint64_t id_data = <uint64_t>hash(data)
        userdatas = self.reply_userdata.get(id_data, None)
        if userdatas is not None:
            userdatas.observed = False
            if userdatas.counter <= 0:
                del self.reply_userdata[id_data]
        cdef int err
        with nogil:
            err = mpv_unobserve_property(
                self._ctx,
                id_data,
            )
        return err

    def shutdown(self):
        if self._ctx == NULL:
            return
        cdef uint64_t ctxid = <uint64_t>id(self)
        with nogil:
            mpv_terminate_destroy(self._ctx)
        self.callbackthread.shutdown()
        del _callbacks[ctxid]
        del _reply_userdatas[ctxid]
        self.callback = None
        self.reply_userdata = None
        self._ctx = NULL

    # def opengl_cb_api(self):
    #     cdef void *cb

    #     _ctx = mpv_get_sub_api(self._ctx, MPV_SUB_API_OPENGL_CB)
    #     if not _ctx:
    #         raise MPVError("OpenGL API not available")

    #     ctx = OpenGLContext()
    #     ctx._ctx = <mpv_opengl_cb_context*>_ctx

    #     return ctx

    def __dealloc__(self):
        self.shutdown()

cdef void *_c_getprocaddress(void *ctx, const char *name) with gil:
    return <void *><intptr_t>(<object>ctx)(name)

cdef void _c_updatecb(void *ctx) with gil:
    (<object>ctx)()

# cdef class OpenGLContext(object):
#     cdef:
#         mpv_opengl_cb_context *_ctx
#         bint inited
#         object update_cb

#     def __init__(self):
#         self.inited = False
#         warnings.warn("OpenGLContext is deprecated, please switch to RenderContext", DeprecationWarning)

#     def init_gl(self, exts, get_proc_address):
#         exts = _strenc(exts) if exts is not None else None
#         cdef char* extsc = NULL
#         if exts is not None:
#             extsc = exts
#         with nogil:
#             err = mpv_opengl_cb_init_gl(self._ctx, extsc, &_c_getprocaddress,
#                                         <void *>get_proc_address)
#         if err < 0:
#             raise MPVError(err)

#         self.inited = True

#     def set_update_callback(self, cb):
#         self.update_cb = cb
#         with nogil:
#             mpv_opengl_cb_set_update_callback(self._ctx, &_c_updatecb, <void *>cb)

#     def draw(self, fbo, w, h):
#         cdef:
#             int fboc = fbo
#             int wc = w
#             int hc = h
#         with nogil:
#             err = mpv_opengl_cb_draw(self._ctx, fboc, wc, hc)
#         if err < 0:
#             raise MPVError(err)

#     def report_flip(self, time):
#         cdef int64_t ctime = time
#         with nogil:
#             err = mpv_opengl_cb_report_flip(self._ctx, ctime)
#         if err < 0:
#             raise MPVError(err)

#     def uninit_gl(self):
#         if not self.inited:
#             return
#         with nogil:
#             err = mpv_opengl_cb_uninit_gl(self._ctx)
#         if err < 0:
#             raise MPVError(err)
#         self.inited = False

#     def __dealloc__(self):
#         self.uninit_gl()

DEF MAX_RENDER_PARAMS = 32

cdef class _RenderParams(object):
    cdef:
        mpv_render_param params[MAX_RENDER_PARAMS + 1]
        object owned

    def __init__(self):
        self.owned = []
        self.params[0].type = MPV_RENDER_PARAM_INVALID

    cdef add_voidp(self, mpv_render_param_type t, void *p, bint owned=False):
        count = len(self.owned)
        if count >= MAX_RENDER_PARAMS:
            if owned:
                free(p)
            raise PyMPVError("RenderParams overflow")

        self.params[count].type = t
        self.params[count].data = p
        self.params[count + 1].type = MPV_RENDER_PARAM_INVALID
        self.owned.append(owned)

    cdef add_int(self, mpv_render_param_type t, int val):
        cdef int *p = <int *>malloc(sizeof(int))
        p[0] = val
        self.add_voidp(t, p)

    cdef add_string(self, mpv_render_param_type t, char *s):
        cdef char *p = <char *>malloc(strlen(s) + 1)
        strcpy(p, s)
        self.add_voidp(t, p)

    def __dealloc__(self):
        for i, j in enumerate(self.owned):
            if j:
                free(self.params[i].data)

cdef void *get_pointer(const char *name, object obj):
    cdef void *p
    if PyCapsule_IsValid(obj, name):
        p = PyCapsule_GetPointer(obj, name)
    elif isinstance(obj, int) or isinstance(obj, long) and obj:
        p = <void *><intptr_t>obj
    else:
        raise PyMPVError("Unknown or invalid pointer object: %r" % obj)
    return p

@cython.internal
cdef class RenderFrameInfo(object):
    cdef _from_struct(self, mpv_render_frame_info *info):
        self.present = bool(info[0].flags & MPV_RENDER_FRAME_INFO_PRESENT)
        self.redraw = bool(info[0].flags & MPV_RENDER_FRAME_INFO_REDRAW)
        self.repeat = bool(info[0].flags & MPV_RENDER_FRAME_INFO_REPEAT)
        self.block_vsync = bool(info[0].flags & MPV_RENDER_FRAME_INFO_BLOCK_VSYNC)
        self.target_time = info[0].target_time
        return self

cdef class RenderContext(object):
    API_OPENGL = "opengl"
    UPDATE_FRAME = MPV_RENDER_UPDATE_FRAME

    cdef:
        Context _mpv
        mpv_render_context *_ctx
        object update_cb
        object _x11_display
        object _wl_display
        object _get_proc_address
        bint inited

    def __init__(self, mpv,
                 api_type,
                 opengl_init_params=None,
                 advanced_control=False,
                 x11_display=None,
                 wl_display=None,
                 drm_display=None,
                 drm_osd_size=None
                 ):

        cdef:
            mpv_opengl_init_params gl_params
            mpv_opengl_drm_params drm_params
            mpv_opengl_drm_osd_size _drm_osd_size

        self._mpv = mpv

        memset(&gl_params, 0, sizeof(gl_params))
        memset(&drm_params, 0, sizeof(drm_params))
        memset(&_drm_osd_size, 0, sizeof(_drm_osd_size))

        params = _RenderParams()

        if api_type == self.API_OPENGL:
            params.add_string(MPV_RENDER_PARAM_API_TYPE, MPV_RENDER_API_TYPE_OPENGL)
        else:
            raise PyMPVError("Unknown api_type %r" % api_type)

        if opengl_init_params is not None:
            self._get_proc_address = opengl_init_params["get_proc_address"]
            gl_params.get_proc_address = &_c_getprocaddress
            gl_params.get_proc_address_ctx = <void *>self._get_proc_address
            params.add_voidp(MPV_RENDER_PARAM_OPENGL_INIT_PARAMS, &gl_params)
        if advanced_control:
            params.add_int(MPV_RENDER_PARAM_ADVANCED_CONTROL, 1)
        if x11_display:
            self._x11_display = x11_display
            params.add_voidp(MPV_RENDER_PARAM_X11_DISPLAY, get_pointer("Display", x11_display))
        if wl_display:
            self._wl_display = wl_display
            params.add_voidp(MPV_RENDER_PARAM_WL_DISPLAY, get_pointer("wl_display", wl_display))
        if drm_display:
            drm_params.fd = drm_display.get("fd", -1)
            drm_params.crtc_id = drm_display.get("crtc_id", -1)
            drm_params.connector_id = drm_display.get("connector_id", -1)
            arp = drm_display.get("atomic_request_ptr", None)
            if arp is not None:
                drm_params.atomic_request_ptr = <_drmModeAtomicReq **>get_pointer(arp, "drmModeAtomicReq*")
            drm_params.render_fd = drm_display.get("render_fd", -1)
            params.add_voidp(MPV_RENDER_PARAM_DRM_DISPLAY, &drm_params)
        if drm_osd_size:
            _drm_osd_size.width, _drm_osd_size.height = drm_osd_size
            params.add_voidp(MPV_RENDER_PARAM_DRM_OSD_SIZE, &_drm_osd_size)

        err = mpv_render_context_create(&self._ctx, self._mpv._ctx, params.params)
        if err < 0:
            raise MPVError(err)
        self.inited = True

    @_errors
    def set_icc_profile(self, icc_blob):
        cdef:
            mpv_render_param param
            mpv_byte_array val
            int err

        if not isinstance(icc_blob, bytes):
            raise PyMPVError("icc_blob should be a bytes instance")
        val.data = <void *><char *>icc_blob
        val.size = len(icc_blob)

        param.type = MPV_RENDER_PARAM_ICC_PROFILE
        param.data = &val

        with nogil:
            err = mpv_render_context_set_parameter(self._ctx, param)
        return err

    @_errors
    def set_ambient_light(self, lux):
        cdef:
            mpv_render_param param
            int val
            int err

        val = lux
        param.type = MPV_RENDER_PARAM_AMBIENT_LIGHT
        param.data = &val

        with nogil:
            err = mpv_render_context_set_parameter(self._ctx, param)
        return err

    def get_next_frame_info(self):
        cdef:
            mpv_render_frame_info info
            mpv_render_param param

        param.type = MPV_RENDER_PARAM_NEXT_FRAME_INFO
        param.data = &info
        with nogil:
            err = mpv_render_context_get_info(self._ctx, param)
        if err < 0:
            raise MPVError(err)

        return RenderFrameInfo()._from_struct(&info)

    def set_update_callback(self, cb):
        with nogil:
            mpv_render_context_set_update_callback(self._ctx, &_c_updatecb, <void *>cb)
        self.update_cb = cb

    def update(self):
        cdef uint64_t ret
        with nogil:
            ret = mpv_render_context_update(self._ctx)
        return ret

    @_errors
    def render(self,
               opengl_fbo=None,
               flip_y=False,
               depth=None,
               block_for_target_time=True,
               skip_rendering=False):

        cdef:
            mpv_opengl_fbo fbo

        params = _RenderParams()

        if opengl_fbo:
            memset(&fbo, 0, sizeof(fbo))
            fbo.fbo = opengl_fbo.get("fbo", 0) or 0
            fbo.w = opengl_fbo["w"]
            fbo.h = opengl_fbo["h"]
            fbo.internal_format = opengl_fbo.get("internal_format", 0) or 0
            params.add_voidp(MPV_RENDER_PARAM_OPENGL_FBO, &fbo)
        if flip_y:
            params.add_int(MPV_RENDER_PARAM_FLIP_Y, 1)
        if depth is not None:
            params.add_int(MPV_RENDER_PARAM_DEPTH, depth)
        if not block_for_target_time:
            params.add_int(MPV_RENDER_PARAM_BLOCK_FOR_TARGET_TIME, 0)
        if skip_rendering:
            params.add_int(MPV_RENDER_PARAM_SKIP_RENDERING, 1)

        with nogil:
            ret = mpv_render_context_render(self._ctx, params.params)
        return ret

    def report_swap(self):
        with nogil:
            mpv_render_context_report_swap(self._ctx)

    def free(self):
        if not self.inited:
            return
        with nogil:
            mpv_render_context_free(self._ctx)
        self.inited = False

    def close(self):
        if not self.inited:
            return
        with nogil:
            mpv_render_context_free(self._ctx)
        self.inited = False

    def __dealloc__(self):
        self.close()

cdef class OpenGLRenderContext(RenderContext):
    def __init__(self, mpv,
                 get_proc_address,
                 *args, **kwargs):
        init_params = {
            "get_proc_address": get_proc_address
        }
        RenderContext.__init__(self, mpv, RenderContext.API_OPENGL,
                               init_params, *args, **kwargs)

class CallbackThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.lock = Semaphore()
        self.lock.acquire(True)
        self.callback = None
        self.isshutdown = False

    def shutdown(self):
        self.isshutdown = True
        self.callback = None
        self.lock.release()

    def call(self):
        self.lock.release()

    def set(self, callback):
        self.callback = callback

    def run(self):
        while not self.isshutdown:
            self.lock.acquire(True)
            self.mpv_callback(self.callback) if self.callback else None

    def mpv_callback(self, callback):
        try:
            callback()
        except Exception as e:
            sys.stderr.write("pympv error during callback: %s\n" % e)

cdef void _c_callback(void* d) with gil:
    cdef uint64_t name = <uint64_t>d
    callback = _callbacks.get(name)
    callback.call()
