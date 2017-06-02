import logging
import threading

import mpv
from .base import AbstractTemplate

log = logging.getLogger(__name__)


class MpvTemplate(AbstractTemplate, mpv.Mpv):
    """Bases: :obj:`AbstractTemplate<mpv.templates.AbstractTemplate>`,
    :obj:`Mpv <mpv.Mpv>`.

    A Template that can be subclassed. It uses a :obj:`threading.Thread`
    for the event loop.

    Args:
        options (:obj:`dict`, optional): dictionary of options to set with
            mpv_set_option().
        observe (:obj:`list` of :obj:`str`): a list of properties to be
            observed.
        log_level (:obj:`mpv.LogLevel`): the log level for mpv to use.
        log_handler (:obj:`callable`): a function that will be called with
            the log message as its only argument.
        **kwargs (optional): options to set with mpv_set_option().

    Raises:
        mpv.ApiVersionError: if the loaded libmpv doesn't meet the minimum
            requirement.

    """

    def __init__(self, options=None, observe=None, log_level=mpv.LogLevel.INFO,
                 log_handler=None, **kwargs):
        super().__init__(options=options, **kwargs)

        if observe is not None:
            for prop in observe:
                self.observe_property(prop)

        if log_handler is not None:
            self.request_log_messages(log_level)
            self.log_handler = log_handler

        self.before_initialize()
        self.initialize()

        self._lock = threading.RLock()
        self._event_condition = threading.Condition(self._lock)
        self._event_loop = threading.Thread(target=self._event_loop,
                                            name='MPVEventHandlerThread')
        self._event_loop.start()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._event_loop.join()

    def exit(self):
        """ """
        self.command('quit')
        self._event_loop.join()

    def _event_loop(self):
        log.debug('Event loop: starting.')
        while self.handle:
            event = self.wait_event(-1)
            if event.event_id in [mpv.EventID.NONE, mpv.EventID.SHUTDOWN]:
                log.debug('Event loop: {}'.format(event.event_id.name))
                self.detach_destroy()
            self._handle_event(event)

            with self._event_condition:
                self._event_condition.notify_all()
