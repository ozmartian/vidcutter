from .template import MpvTemplate

from .base import AbstractTemplate

try:
    from .templateqt import MpvTemplatePyQt
except (ImportError, NameError) as e:
    pass
