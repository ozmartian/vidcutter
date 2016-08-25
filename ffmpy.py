import errno
import os
import shlex
import subprocess
import sys

__version__ = '0.1.1' # pete@ozmartians.com -> updates for better integration with PyInstaller


class FFmpeg(object):
    """Wrapper for various `ffmpeg <https://www.ffmpeg.org/>`_ related applications (ffmpeg,
    ffprobe).
    """

    def __init__(self, executable='ffmpeg', global_options='', inputs=None, outputs=None):
        """Initialize wrapper object.

        Compiles FFmpegg command line from passed arguments (executable path, options, inputs and
        outputs). FFmpeg executable by default is taken from ``PATH`` but can be overridden with an
        absolute path. For more info about FFmpeg command line format see
        `here <https://ffmpeg.org/ffmpeg.html#Synopsis>`_.

        :param str executable: ffmpeg executable; can either be ``ffmpeg`` command that will be found
            in ``PATH`` (the default) or an absolute path to ``ffmpeg`` executable
        :param iterable global_options: global options passed to ``ffmpeg`` executable (e.g.
            ``-y``, ``-v`` etc.); can be specified either as a list/tuple of strings, or a
            space-separated string
        :param dict inputs: a dictionary specifying one or more inputs as keys with their
            corresponding options as values
        :param dict outputs: a dictionary specifying one or more outputs as keys with their
            corresponding options as values
        """
        self.executable = executable
        self._cmd = [executable]
        if not _is_sequence(global_options):
            global_options = shlex.split(global_options)
        self._cmd += global_options
        self._cmd += self._merge_args_opts(inputs, add_input_option=True)
        self._cmd += self._merge_args_opts(outputs)
        self.cmd = subprocess.list2cmdline(self._cmd)

    def __repr__(self):
        return '<{0!r} {1!r}>'.format(self.__class__.__name__, self.cmd)

    def _merge_args_opts(self, args_opts_dict, **kwargs):
        """Merge options with their corresponding arguments.

        Iterates over the dictionary holding arguments (keys) and options (values). Merges each
        options string with its corresponding argument.

        :param dict args_opts_dict: a dictionary of arguments and options
        :param dict kwargs: *input_option* - if specified prepends ``-i`` to input argument
        :return: merged list of strings with arguments and their corresponding options
        :rtype: list
        """
        merged = []

        if not args_opts_dict:
            return merged

        for arg, opt in args_opts_dict.items():
            if not _is_sequence(opt):
                opt = shlex.split(opt or '')
            merged += opt

            if not arg:
                continue
            if 'add_input_option' in kwargs:
                merged.append('-i')

            merged.append(arg)

        return merged

    def run(self, input_data=None, verbose=False):
        """Run ffmpeg command and get its output.

        If ``pipe`` protocol is used for input, `input_data` should contain data to be passed as
        input to ``STDIN``. If ``pipe`` protocol is used for output, output data will be read from
        ``STDOUT`` and returned. More infor about ``pipe`` protocol `here
        <https://ffmpeg.org/ffmpeg-protocols.html#pipe>`_.

        :param str input_data: media (audio, video, transport stream) data as a byte string (e.g. the
            result of reading a file in binary mode)
        :param bool verbose: show ffmpeg output
        :return: output of ffmpeg command as a byte string
        :rtype: str
        :raise: :class:`~.utils.ff.exceptions.FFRuntimeError` in case ffmpeg command fails
        """
        if verbose:
            stdout = stderr = None
        else:
            stdout = stderr = subprocess.PIPE

        try:
            if sys.platform == 'win32':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                ff_command = subprocess.Popen(
                    self._cmd,
                    stdin=subprocess.PIPE,
                    stdout=stdout,
                    stderr=stderr,
                    startupinfo=si,
                    env=os.environ,
                    shell=False
                )
            else:
                ff_command = subprocess.Popen(
                    self._cmd,
                    stdin=subprocess.PIPE,
                    stdout=stdout,
                    stderr=stderr
                )
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise FFExecutableNotFoundError("Executable '{0}' not found".format(self.executable))

        out = ff_command.communicate(input=input_data)
        if ff_command.returncode != 0:
            raise FFRuntimeError(
                "'{cmd}' exited with status {exit_code}\n\n{out}".format(
                    cmd=self.cmd,
                    exit_code=ff_command.returncode,
                    out=out[1]
                )
            )

        if out[0]:
            return out[0]
        else:
            return None


class FFprobe(FFmpeg):
    """Wrapper for `ffprobe <https://www.ffmpeg.org/ffprobe.html>`_."""

    def __init__(self, executable='ffprobe', global_options='', inputs=None):
        """Create an instance of FFprobe.

        Compiles FFprobe command line from passed arguments (executable path, options, inputs).
        FFprobe executable by default is taken from ``PATH`` but can be overridden with an
        absolute path. For more info about FFprobe command line format see
        `here <https://ffmpeg.org/ffprobe.html#Synopsis>`_.

        :param str executable: absolute path to ffprobe executable
        :param iterable global_options: global options passed to ffmpeg executable; can be specified
            either as a list/tuple of strings or a space-separated string
        :param dict inputs: a dictionary specifying one or more inputs as keys with their
            corresponding options as values
        """
        super(FFprobe, self).__init__(
            executable=executable,
            global_options=global_options,
            inputs=inputs
        )


class FFExecutableNotFoundError(Exception):
    """Raise when ffmpeg/ffprobe executable was not found"""


class FFRuntimeError(Exception):
    """Raise when FFmpeg/FFprobe run fails."""


def _is_sequence(obj):
    """Check if the object is a sequence (list, tuple etc.).

    :param object obj: an object to be checked
    :return: True if the object is iterable but is not a string, False otherwise
    :rtype: bool
    """
    return hasattr(obj, '__iter__') and not isinstance(obj, str)
