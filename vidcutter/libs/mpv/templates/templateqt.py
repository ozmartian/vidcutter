import logging

from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

import vidcutter.libs.mpv.api as mpv
import vidcutter.libs.mpv.events as events
import vidcutter.libs.mpv.types as types

from .base import AbstractTemplate

log = logging.getLogger(__name__)


class EventWorker(QObject):
    mpv_event = pyqtSignal(events.Event)
    finished = pyqtSignal()

    def wait_event(self, mpv_instance):
        log.debug('Event loop: starting.')
        while mpv_instance.handle:
            event = mpv_instance.wait_event(-1)
            if event.event_id == types.EventID.NONE:
                log.debug('Event loop: None event.')
            elif event.event_id == types.EventID.SHUTDOWN:
                log.debug('Event loop: Shutdown event.')
                self.mpv_event.emit(event)
                break
            self.mpv_event.emit(event)
        log.debug('Event loop: returning.')
        self.finished.emit()


class MpvTemplatePyQt(QObject, AbstractTemplate, mpv.Mpv):
    """Bases: :obj:`QObject <PyQt5.QtCore.QObject>`,
    :obj:`AbstractTemplate<mpv.templates.AbstractTemplate>`,
    :obj:`Mpv <mpv.Mpv>`.

    A Template that can be subclassed for a PyQt5 application.
    It uses a :obj:`PyQt5.QtCore.QThread` for the event loop.
    see ``demo/pyqt5.py`` for an example.

    Args:
        options (:obj:`dict`, optional): dictionary of options to set with
            mpv_set_option().
        observe (:obj:`list` of :obj:`str`): a list of properties to be
            observed.
        log_level (:obj:`mpv.LogLevel`): the log level for mpv to use.
        log_handler (:obj:`callable`): a function that will be called with
            the log message as its only argument.
        parent (:obj:`QObject <PyQt5.QtCore.QObject>`): the Qt parent.
        **kwargs (optional): options to set with mpv_set_option().

    Raises:
        mpv.ApiVersionError: if the loaded libmpv doesn't meet the minimum
            requirement.

    Attributes:
        shutdown (:obj:`pyqtSignal <PyQt5.QtCore.pyqtSignal>`): Emitted when
            mpv has finished shutting down after
            :obj:`quit() <mpv.templates.MpvTemplatePyQt.quit>` has been called.

    """
    _wakeup = pyqtSignal(mpv.Mpv)
    shutdown = pyqtSignal()

    def __init__(self, options=None, observe=None, log_level=types.LogLevel.INFO,
                 log_handler=None, parent=None, **kwargs):
        QObject.__init__(self, parent)
        AbstractTemplate.__init__(self)
        mpv.Mpv.__init__(self, options=options, **kwargs)

        if observe is not None:
            for prop in observe:
                self.observe_property(prop)

        if log_handler is not None:
            self.request_log_messages(log_level)
            self.log_handler = log_handler

        self._event_thread = QThread(self)
        self._event_worker = EventWorker()
        self._event_worker.moveToThread(self._event_thread)
        self._event_worker.mpv_event.connect(self._handle_event)
        self._event_worker.finished.connect(self._event_worker.deleteLater)
        self._event_thread.finished.connect(self._event_thread.deleteLater)
        self._wakeup.connect(self._event_worker.wait_event)

        self.before_initialize()
        self.initialize()

        self._event_thread.start()
        self._wakeup.emit(self)

    def quit(self):
        """Make mpv quit. """
        if self.handle:
            self.command('quit')  # trigger a SHUTDOWN event.
            self._event_thread.quit()  # end the event thread
            self._event_thread.wait()
            self.terminate_destroy()  # destroy mpv
        self.shutdown.emit()

    @pyqtSlot(int)
    def seek_absolute(self, ms):
        """
        Args:
            ms (int): seek to the absolute position in milliseconds.

        """
        if not self.handle:
            return
        self.seek(ms / 1000.0, 'absolute+exact')

    @pyqtSlot(int)
    def seek_relative(self, ms):
        """
        Args:
            ms (int): seek relative to the current position in milliseconds.

        """
        if not self.handle:
            return
        self.seek(ms / 1000.0, 'relative+exact')

    @pyqtSlot(float)
    def set_volume(self, val):
        """
        Args:
            val (float) [0, 100]: volume percentage as a float.

        """
        if not self.handle:
            return
        if val < 0 or val > 100:
            raise ValueError('Must be in range [0, 100]')
        self.volume = val
