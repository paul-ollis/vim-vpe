"""Very common code."""

from __future__ import annotations

from typing import Any, Callable, Union
import functools
import re

import vim as _vim

__api__ = [
    'vim_command', 'vim_eval',
]
__all__ = [
    'VimError', 'vim_command',
]


class VimError(_vim.error, Exception):
    """A parsed version of vim.error.

    VPE code raises this in place of the standard vim.error exception. It is
    a subclass of vim.error, so code that handles vime.error will still work
    when converted to use the `vpe.vim` object.

    This exception attempts to parse the Vim error string to provide additional
    attributes:

    @command: The name of the Vim command that raised the error. This may be
              an empty string.
    @code:    The error code. This will be zero if parsing failed to extract
              the code.
    @message: The message part, after extracting the command, error code and
              'Vim' prefix. If parsing completely fails then is simply the
              unparsed message.
    """
    command: str
    code: int
    message: str

    def __init__(self, error: _vim.error):
        super().__init__(str(error))
        self.message: str
        self.command: str = ''
        self.code: int = 0
        pat = r'''(?x)
            Vim                           # Common prefix.
            (?:
                \( (?P<command> \w+ ) \)  # May have command in parentheses.
            ) ?
            :
            (?:
                E (?P<code> \d{1,4} )     # May have an error code.
            :
            ) ?
            [ ] (?P<message> .* )         # Space then free form message.
        '''
        m = re.match(pat, str(error))
        if m:
            code = m.group('code')
            self.code = int(code) if code else 0
            self.command = m.group('command') or ''
            self.message = m.group('message')
        else:
            self.message = str(error)


def invoke_vim_function(func: Callable, *args) -> Any:
    """Invoke a Vim function, converting the vim.errro to VimError.

    :func:   The function to invoke.
    :args:   Positional arguments, passed unmodified.
    """
    try:
        return func(*args)
    except _vim.error as e:
        raise VimError(e)  # pylint: disable=raise-missing-from


_eval_func = _vim.Function('eval')

vim_command = functools.partial(invoke_vim_function, _vim.command)
vim_simple_eval = functools.partial(invoke_vim_function, _vim.eval)
vim_eval = functools.partial(invoke_vim_function, _eval_func)
