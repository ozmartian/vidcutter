__title__ = 'mpv'
__version__ = '0.3.0'
__libmpv_version__ = (1, 20)

# Set default logging handler to avoid "No handler found" warnings.
import logging

from .api import Mpv
from .exceptions import MpvError, ApiVersionError, LibraryNotLoadedError
from .properties import PROPERTIES
from .types import LogLevel, Format, EventID, ErrorCode, EndFileReason, SubApi

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
