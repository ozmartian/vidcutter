import logging

from . import __libmpv_version__
from .exceptions import MpvError, ApiVersionError, LibraryNotLoadedError
from .libmpv import LibMPV
from .properties import PROPERTIES

log = logging.getLogger(__name__)


class Mpv(object):
    """Create an MPV instance. Any kwargs given will be passed to mpv as
    options. The instance must be initialized with
    :obj:`initialize() <mpv.Mpv.initialize()>`.

    Args:
        name (str, optional): the `name` argument for :obj:`ctypes.CDLL`.wz
        options (dict, optional): dictionary of options to set with
            mpv_set_option().
        **kwargs (optional): options to send to mpv via mpv_set_option() before
            the handle is initialized. Use underscores in place of hyphens.

    Raises:
        mpv.LibraryNotLoadedError: if libmpv can't be loaded.
        mpv.ApiVersionError: if the loaded libmpv doesn't meet the minimum
            requirement.

    Attributes:
        handle: the mpv handle.

    """

    def __init__(self, name=None, options=None, **kwargs):
        try:
            self.libmpv = LibMPV(name)
        except Exception as e:
            raise LibraryNotLoadedError(e)

        version = self.api_version()
        if version < __libmpv_version__:
            raise ApiVersionError(version)

        self.handle = self.libmpv.mpv_create()
        self.opengl = None

        if options is not None:
            for k, v in options.items():
                try:
                    self.libmpv.set_option(self.handle, k, v)
                except MpvError as e:
                    log.debug(e)

        for k, v in kwargs.items():
            try:
                self.libmpv.set_option(self.handle, k.replace('_', '-'), v)
            except MpvError as e:
                log.debug(e)

    def initialize(self):
        """Initialize the mpv instance. This function needs to be called to
        make full use of the client API

        """
        self.libmpv.mpv_initialize(self.handle)

    def set_option(self, option, value):
        """
        Args:
            option (str): Option name. This is the same as on the mpv command
                line, but without the leading "--".
            value: Option value.

        Raises:
            mpv.MpvError

        """
        self.libmpv.set_option(self.handle, option, value)

    def api_version(self):
        """Return the api version. see: `Client API Changes`_.

        Returns:
            :obj:`tuple`: libmpv version (major, minor)

        .. _Client API Changes:
           https://github.com/mpv-player/mpv/blob/master/DOCS/
           client-api-changes.rst

        """
        return self.libmpv.client_api_version()

    def wait_event(self, timeout=-1):
        """Wait for the next event, or until the timeout expires, or if
        another thread makes a call to mpv_wakeup(). Passing 0 as timeout will
        never wait, and is suitable for polling.

        Args:
            timeout (float, optional): Timeout in seconds, after which the
                function returns even if no event was received.
                A MPV_EVENT_NONE is returned on timeout. A value of 0 will
                disable waiting. Negative values will wait with an infinite
                timeout.

        Returns:
            :obj:`Event <mpv.events.Event>`

        """
        e = self.libmpv.mpv_wait_event(self.handle, timeout)
        return e.contents.as_object()

    def set_wakeup_callback(self, func, data):
        self.libmpv.set_wakeup_callback(self.handle, func, data)

    def terminate_destroy(self):
        """ """
        self.handle, handle = None, self.handle
        self.libmpv.mpv_terminate_destroy(handle)

    def detach_destroy(self):
        """ """
        self.handle, handle = None, self.handle
        self.libmpv.mpv_detach_destroy(handle)

    def request_log_messages(self, level):
        """Enable or disable receiving of log messages.

        Args:
            level (:obj:`mpv.LogLevel`): The log level mpv will use.

        """
        self.libmpv.mpv_request_log_messages(self.handle, level.encode())

    def available_properties(self):
        """
        Returns:
            list: names of properties that can be accessed.

        """
        return list(set(self.property_list).intersection(PROPERTIES.keys()))

    def unavailable_properties(self):
        """
        Returns:
            list: names of properties that cannot be accessed.

        """
        return list(set(self.property_list).difference(PROPERTIES.keys()))

    def observe_property(self, name, mpv_format=None, reply_userdata=0):
        """Get a notification whenever the given property changes.

        Args:
            name (str): the name of the property.
            mpv_format (:obj:`mpv.Format`, optional): The format of the
                data.
            reply_userdata (int, optional): This will be used for the
                mpv_event.reply_userdata field for the received
                MPV_EVENT_PROPERTY_CHANGE events.

        Raises:
            AttributeError: if the property isn't available.
            mpv.MpvError

        """
        if name not in PROPERTIES:
            raise AttributeError('Property "{}" not available.'.format(name))
        if mpv_format is None:
            mpv_format = PROPERTIES[name][0]
        self.libmpv.mpv_observe_property(self.handle, reply_userdata,
                                         name.encode(), mpv_format)

    def unobserve_property(self, reply_userdata):
        """Undo observe_property(). This will remove all observed properties
        for which the given number was passed as reply_userdata to
        observe_property.

        Args:
            reply_userdata (int): reply_userdata that was passed to
                observe_property.

        """
        self.libmpv.mpv_unobserve_property(self.handle, reply_userdata)

    def command(self, *args):
        """Send a command to the player. Commands are the same as those used
        in ``input.conf``. see: `Input Commands`_.

        Example:
        ::

            mpv.command('loadfile', 'test.mp4', 'replace', 'start=+100,vid=no')

        Args:
            *args: strings.

        .. _Input Commands:
            https://mpv.io/manual/master/#list-of-input-commands

        """
        self.libmpv.command(self.handle, *args)

    def command_node(self, *args):
        """Send a command to the player. Commands are the same as those used
        in ``input.conf``. see: `Input Commands`_.

        Example:
        ::

            mpv.command_node('loadfile', 'test.mp4', 'replace', {
                'start': '+100',
                'vid': 'no'
            })

        Args:
            *args: arguments in any basic type.

        """
        return self.libmpv.command_node(self.handle, *args)

    def get_opengl_api(self):
        self.opengl = self.libmpv.opengl_get_sub_api(self.handle)

    def opengl_set_update_callback(self, callback, ctx=None):
        self.libmpv.opengl_cb_set_update_callback(self.opengl, callback, ctx)

    def opengl_report_flip(self):
        self.libmpv.opengl_cb_report_flip(self.opengl)

    def opengl_init_gl(self, get_proc_address, exts=None, ctx=None):
        self.libmpv.opengl_cb_init_gl(self.opengl, exts, get_proc_address, ctx)

    def opengl_uninit_gl(self):
        self.libmpv.opengl_cb_uninit_gl(self.opengl)

    def opengl_draw(self, fbo, w, h):
        self.libmpv.opengl_draw(self.opengl, fbo, w, h)

    def show_text(self, string, duration='-', level=None):
        self.command('show_text', string, duration, level)

    def seek(self, seconds, method='relative+exact'):
        """Shortcut for a ``seek`` :obj:`command() <mpv.Mpv.command>`"""
        self.command_node('seek', seconds, method)

    def play(self, filename):
        """Shortcut for a ``loadfile`` :obj:`command() <mpv.Mpv.command>`"""
        self.command_node('loadfile', filename, 'replace')

    def quit(self, code=None):
        """Shortcut for a ``quit`` :obj:`command() <mpv.Mpv.command>`"""
        self.command('quit', code)


def _bindproperty(cls, name, proptype, access):
    def getter(self):
        return self.libmpv._get_property(self.handle, name, proptype)

    def setter(self, value):
        self.libmpv._set_property(self.handle, name, proptype, value)

    def barf(*args):
        raise NotImplementedError('Access denied')

    setattr(cls, name.replace('-', '_'),
            property(getter if 'r' in access else barf,
                     setter if 'w' in access else barf))


for name, (proptype, access) in PROPERTIES.items():
    _bindproperty(Mpv, name, proptype, access)
