import logging
from ctypes import (c_void_p, c_int, c_longlong, c_ulonglong, addressof, cast,
                    c_char_p, c_size_t, c_double, Structure, Union, POINTER,
                    CFUNCTYPE)
from .events import Event, ClientMessage, EndFile, LogMessage, Property


log = logging.getLogger(__name__)


class MpvHandle(c_void_p):
    pass


class MpvOpenGLCbContext(c_void_p):
    pass


class Enum(c_int):
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        else:
            return self.value == other

    @property
    def name(self):
        for k, v in self.__class__.__dict__.items():
            if v == self.value:
                return k
        raise ValueError(self.value)


class SubApi(Enum):
    """This is used for additional APIs that are not strictly part of the core
    API.

    """
    MPV_SUB_API_OPENGL_CB = 1  #:


class ErrorCode(Enum):
    """ For documentation on these, see ``libmpv/client.h`` """
    SUCCESS = 0  #:
    EVENT_QUEUE_FULL = -1  #:
    NOMEM = -2  #:
    UNINITIALIZED = -3  #:
    INVALID_PARAMETER = -4  #:
    OPTION_NOT_FOUND = -5  #:
    OPTION_FORMAT = -6  #:
    OPTION_ERROR = -7  #:
    PROPERTY_NOT_FOUND = -8  #:
    PROPERTY_FORMAT = -9  #:
    PROPERTY_UNAVAILABLE = -10  #:
    PROPERTY_ERROR = -11  #:
    COMMAND = -12  #:
    LOADING_FAILED = -13  #:
    AO_INIT_FAILED = -14  #:
    VO_INIT_FAILED = -15  #:
    NOTHING_TO_PLAY = -16  #:
    UNKNOWN_FORMAT = -17  #:
    UNSUPPORTED = -18  #:
    NOT_IMPLEMENTED = -19  #:


class Format(Enum):
    NONE = 0  #:
    STRING = 1  #:
    OSD_STRING = 2  #:
    FLAG = 3  #:
    INT64 = 4  #:
    DOUBLE = 5  #:
    NODE = 6  #:
    NODE_ARRAY = 7
    NODE_MAP = 8
    BYTE_ARRAY = 9

    def ctype(self):
        return [None, c_char_p, c_char_p, c_int, c_longlong, c_double,
                MpvNode, MpvNodeList, MpvNodeList, MpvByteArray][self.value]

    def decode(self, obj):
        if self.value == Format.NONE:
            return None
        elif self.value == Format.NODE:
            return obj.get_value()
        elif self.value in [Format.STRING, Format.OSD_STRING]:
            return obj.value.decode()
        elif self.value == Format.FLAG:
            return bool(obj.value)
        elif self.value == Format.DOUBLE:
            return float(obj.value)
        else:
            return obj.value

    def encode(self, value):
        ctype = self.ctype()
        val = ctype()
        if self.value in [Format.STRING, Format.OSD_STRING]:
            val.value = value.encode()
        elif self.value == Format.FLAG:
            val.value = int(value)
        elif self.value == Format.INT64:
            val.value = int(value)
        elif self.value == Format.DOUBLE:
            val.value = float(value)
        elif self.value == Format.NODE:
            nb = NodeBuilder(value)
            val = nb.node
        return val


class LogLevel(c_char_p):
    NONE = 'no'  #: disable absolutely all messages.
    FATAL = 'fatal'  #: critical/aborting errors.
    ERROR = 'error'  #: simple errors.
    WARN = 'warn'  #: possible problems.
    INFO = 'info'  #: informational message.
    V = 'v'  #: noisy informational message.
    DEBUG = 'debug'  #: very noisy technical information.
    TRACE = 'trace'  #: extremely noisy.


class MpvNodeList(Structure):

    def __init__(self, is_map, num):
        self.num = num
        v = (MpvNode * num)()
        self.values = cast(v, POINTER(MpvNode))
        if is_map:
            k = (c_char_p * num)()
            self.keys = cast(k, POINTER(c_char_p))

    def as_list(self):
        return [self.values[i] for i in range(self.num)]

    def as_dict(self):
        return {
            self.keys[i].decode(): self.values[i]
            for i in range(self.num)
        }


class MpvByteArray(Structure):
    _fields_ = [('data', c_void_p),
                ('size', c_size_t)]


class _MpvNodeUnion(Union):
    _fields_ = [('string', c_char_p),
                ('flag', c_int),
                ('int64', c_longlong),
                ('double_', c_double),
                ('list', POINTER(MpvNodeList)),
                ('ba', POINTER(MpvByteArray))]


class MpvNode(Structure):
    _anonymous_ = ('u',)
    _fields_ = [('u', _MpvNodeUnion),
                ('format', Format)]

    def get_value(self):
        if self.format.value in [Format.STRING, Format.OSD_STRING]:
            return self.string.decode()
        elif self.format.value == Format.FLAG:
            return bool(self.flag)
        elif self.format.value == Format.INT64:
            return int(self.int64)
        elif self.format.value == Format.DOUBLE:
            return float(self.double_)
        elif self.format.value == Format.NODE_ARRAY:
            return [node.get_value() for node in self.list.contents.as_list()]
        elif self.format.value == Format.NODE_MAP:
            return {key: node.get_value() for key, node in
                    self.list.contents.as_dict().items()}
        elif self.format.value == Format.BYTE_ARRAY:
            raise NotImplementedError
        else:
            return None


MpvNodeList._fields_ = [('num', c_int),
                        ('values', POINTER(MpvNode)),
                        ('keys', POINTER(c_char_p))]


class EndFileReason(Enum):
    EOF = 0  #:
    STOP = 2  #:
    QUIT = 3  #:
    ERROR = 4  #:
    REDIRECT = 5  #:


class EventID(Enum):
    NONE = 0  #:
    SHUTDOWN = 1  #:
    LOG_MESSAGE = 2  #:
    GET_PROPERTY_REPLY = 3  #:
    SET_PROPERTY_REPLY = 4  #:
    COMMAND_REPLY = 5  #:
    START_FILE = 6  #:
    END_FILE = 7  #:
    FILE_LOADED = 8  #:
    TRACKS_CHANGED = 9
    """deprecated: equivalent to using mpv_observe_property() on the
    "track-list" property."""
    TRACK_SWITCHED = 10
    """deprecated: equivalent to using mpv_observe_property() on the "vid",
    "aid", "sid" property."""
    IDLE = 11  #:
    PAUSE = 12
    """deprecated: equivalent to using mpv_observe_property() on the "pause"
    property."""
    UNPAUSE = 13
    """deprecated: equivalent to using mpv_observe_property() on the "pause"
    property."""
    TICK = 14  #:
    SCRIPT_INPUT_DISPATCH = 15
    """deprecated: This event never happens anymore."""
    CLIENT_MESSAGE = 16  #:
    VIDEO_RECONFIG = 17  #:
    AUDIO_RECONFIG = 18  #:
    METADATA_UPDATE = 19
    """deprecated: equivalent to using mpv_observe_property() on the
    "metadata" property."""
    SEEK = 20  #:
    PLAYBACK_RESTART = 21  #:
    PROPERTY_CHANGE = 22  #:
    CHAPTER_CHANGE = 23
    """deprecated: equivalent to using mpv_observe_property() on the "chapter"
    property."""
    QUEUE_OVERFLOW = 24  #:

    def ctype(self):
        if self.value == EventID.LOG_MESSAGE:
            return MpvEventLogMessage
        elif self.value == EventID.END_FILE:
            return MpvEventEndFile
        elif self.value == EventID.SCRIPT_INPUT_DISPATCH:
            return MpvEventScriptInputDispatch
        elif self.value == EventID.CLIENT_MESSAGE:
            return MpvEventClientMessage
        elif self.value == EventID.PROPERTY_CHANGE:
            return MpvEventProperty
        return None


class MpvEvent(Structure):
    _fields_ = [('event_id', EventID),
                ('error', ErrorCode),
                ('reply_userdata', c_ulonglong),
                ('data', c_void_p)]

    def as_object(self):
        dtype = self.event_id.ctype()
        return Event(
            EventID(self.event_id.value),
            ErrorCode(self.error.value),
            self.reply_userdata,
            (cast(self.data, POINTER(dtype)).contents.as_object() if
             dtype else None)
        )


class MpvEventProperty(Structure):
    _fields_ = [('name', c_char_p),
                ('format', Format),
                ('data', c_void_p)]

    def get_data(self):
        if self.format == Format.NONE:
            return None
        dpointer = cast(self.data, POINTER(self.format.ctype()))
        return self.format.decode(dpointer.contents)

    def as_object(self):
        return Property(self.name.decode(), self.get_data())


class MpvEventLogMessage(Structure):
    _fields_ = [('prefix', c_char_p),
                ('level', c_char_p),
                ('text', c_char_p)]

    def as_object(self):
        return LogMessage(
            self.prefix.decode().rstrip('\n'),
            self.level.decode().rstrip('\n'),
            self.text.decode().rstrip('\n')
        )


class MpvEventEndFile(Structure):
    _fields_ = [('reason', EndFileReason),
                ('error', ErrorCode)]

    def as_object(self):
        return EndFile(EndFileReason(self.reason.value),
                       ErrorCode(self.error.value))


class MpvEventScriptInputDispatch(Structure):  # deprecated
    _fields_ = [('arg0', c_int),
                ('type', c_char_p)]

    def as_object(self):
        pass

    def as_dict(self):
        pass


class MpvEventClientMessage(Structure):
    _fields_ = [('num_args', c_int),
                ('args', POINTER(c_char_p))]

    def as_object(self):
        return ClientMessage(
            [self.args[i].decode() for i in range(self.num_args.value)]
        )


WakeupCallback = CFUNCTYPE(None, c_void_p)
OpenGlCbUpdateFn = CFUNCTYPE(None, c_void_p)
OpenGlCbGetProcAddrFn = CFUNCTYPE(c_void_p, c_void_p, c_char_p)


class NodeBuilder(object):
    __slots__ = ['node']

    def __init__(self, value):
        self.node = MpvNode()
        self.node._heap = []
        self.set(self.node, value)

    def set(self, dst, src):
        src_t = type(src)
        if src_t is str:
            dst.format.value = Format.STRING
            dst.string = src.encode()
        elif src_t is bool:
            dst.format.value = Format.FLAG
            dst.flag = int(src)
        elif src_t is int:
            dst.format.value = Format.INT64
            dst.int64 = src
        elif src_t is float:
            dst.format.value = Format.DOUBLE
            dst.double_ = src
        elif src_t in (list, tuple):
            l = MpvNodeList(False, len(src))
            self.node._heap.append(l)
            dst.format.value = Format.NODE_ARRAY
            dst.list = cast(addressof(l), POINTER(MpvNodeList))
            for i, item in enumerate(src):
                self.set(dst.list.contents.values[i], item)
        elif src_t is dict:
            l = MpvNodeList(True, len(src))
            self.node._heap.append(l)
            dst.format.value = Format.NODE_MAP
            dst.list = cast(addressof(l), POINTER(MpvNodeList))
            for i, (k, v) in enumerate(src.items()):
                if type(k) is not str:
                    raise KeyError('Dict keys must be strings.')
                dst.list.contents.keys[i] = k.encode()
                self.set(dst.list.contents.values[i], v)
        else:
            raise TypeError('Unsupported type for a Node.')
