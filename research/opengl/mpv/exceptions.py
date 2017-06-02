from mpv import __libmpv_version__


class MpvError(Exception):
    """
    Attributes:
        func (:obj:`callable`): The function which caused the exception.
        args (:obj:`list`): The arguments to the function.
        error_code (:obj:`mpv.ErrorCode`): The error code.
        reason (:obj:`str`): A string describing the error.

    """

    def __init__(self, func, error_code, reason, args):
        self.func = func
        self.error_code = error_code
        self.reason = reason
        self.args = args

    def __str__(self):
        return '[{code.value} {code.name}] "{reason}". {func}{args}'.format(
            code=self.error_code, func=self.func, reason=self.reason,
            args=self.args
        )


class ApiVersionError(Exception):
    """
    Attributes:
        version (tuple): The version of the library that was loaded.
        target (tuple): The required minimum version.

    """

    def __init__(self, version):
        self.version = version
        self.target = __libmpv_version__

    def __str__(self):
        return 'Your version={}. Target>={}'.format(self.version,
                                                    self.target)


class LibraryNotLoadedError(Exception):
    pass
