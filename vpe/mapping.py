"""Python support for key sequence mapping.

This module provides support for mapping key sequences to Python function
calls.
"""

from typing import Tuple, Optional, List, Callable, Dict, Any

from . import core
from .wrappers import vim

mode_to_map_command = {
    'normal': 'nnoremap',
    'visual': 'xnoremap',
    'op-pending': 'onoremap',
    'insert': 'inoremap',
    # Not supported unless (and until) a valid use-case presents itself.
    # 'command':    cnoremap,
}


class MapCallback(core.Callback):
    """Wrapper for a function to be invoked by a key mapping.

    This extends the core `Callback` to provide a `MappingInfo` as the first
    positional argument.

    :pass_info: If True, provide a MappingInfo object as the first argument to
                the callback function.
    """
    def __init__(self, *args, **kwargs):
        self.pass_info = kwargs.pop('pass_info', False)
        super().__init__(*args, **kwargs)

    def get_call_args(self, _vpe_args: Dict[str, Any]):
        """Get the Python positional and keyword arguments.

        This makes the first positional argument a `MappingInfo` instance,
        unless self.pass_info has been cleared.

        :_vpe_args: The dictionary passed from the Vim domain.
        """
        if self.pass_info:
            info = MappingInfo(*self.extra_kwargs.get('info'))
            py_args = info, *self.py_args
        else:
            py_args = self.py_args
        return py_args, self.py_kwargs


class MappingInfo:
    """Information passed to a key mapping callback handler.

    The initialisation parameters are made available as attributes.

    @mode:         The mode in which the mapping was triggered (normal, visual,
                   op-pending or insert).
    @keys:         The sequence of keys that triggered the mapping.
    @vmode:        The visual mode (character, line or block). Will be ``None``
                   when not applicable.
    @start_cursor: When mode=="visual", a tuple (line, column) of the selection
                   start. Both values are 1-based. Will be (-1, -1) when not
                   applicable.
    @end_cursor:   When mode=="visual", a tuple (line, column) of the selection
                   end. Both values are 1-based. Will be (-1, -1) when not
                   applicable.
    """
    def __init__(self, mode: str, keys: str):
        self.mode: str = mode
        self.keys: str = keys
        self.vmode: Optional[str] = None
        self.start_cursor: Tuple[int, int] = (-1, -1)
        self.end_cursor: Tuple[int, int] = (-1, -1)
        if self.mode == 'visual':
            v = vim.visualmode()
            if v == 'v':
                self.vmode = 'character'
            elif v == 'V':
                self.vmode = 'line'
            else:
                self.vmode = 'block'
            start: List[int] = vim.getpos("'<")
            end: List[int] = vim.getpos("'>")
            self.start_cursor = tuple(start[1:3])    # type: ignore[assignment]
            self.end_cursor = tuple(end[1:3])        # type: ignore[assignment]

    @property
    def line_range(self) -> Optional[Tuple[int, int]]:
        """The line range, if visual mode was active.

        This is a Python style range.
        """
        if self.start_cursor[0] >= 0:
            slidx, _ = self.start_cursor
            elidx, _ = self.end_cursor
            return slidx - 1, elidx
        return None

    def __str__(self):
        return f'{self.__class__.__name__}({self.mode},{self.keys})'


# Special args to consider.
#   script  - Probably not useful.
#   expr    - Probably should have a different function.
def map(
        mode: str, keys: str, func: Callable,
        *, buffer: bool = True, silent: bool = True, unique: bool = False,
        nowait: bool = False, command: bool = False, pass_info=True,
        args=(), kwargs: Optional[dict] = None,
        vim_exprs: Tuple[str, ...] = ()):
    """Set up a key mapping that invokes a Python function.

    By default, the effective map command has the form:

       {m}noremap <buffer> <silent> keys ...

    Where {m} is one of n, x, o, i.

    The noremap form is always used.

    By default the first argument passed to the mapped function is a
    `MappingInfo` object. The *pass_info* argument can be used to prevent this.
    Additional arguments can be speficied using *args* and *kwargs*.

    For convenience, mode specific versions are provided (`nmap`, `xmap`,
    `omap` and `imap`). See those for details of what he mapped function can
    do. It is recommended that these mode specific versions are use in
    preference to this function.

    :mode:      A string defining the mode in which the mapping occurs. This
                should be one of: normal, visual, op-pending, insert, command.
    :keys:      The key sequence to be mapped.
    :func:      The Python function to invoke for the mapping.
    :buffer:    Use the <buffer> special argument. Defaults to True.
    :silent:    Use the <silent> special argument. Defaults to True.
    :unique:    Use the <unique> special argument. Defaults to False.
    :nowait:    Use the <nowait> special argument. Defaults to False.
    :command:   Only applicable to insert mode. If true then the function
                is invoked from the command prompt and the return value is not
                used. Otherwise (the default) the function should return the
                text to be inserted.
    :pass_info: If set then the first argument passed to func is a MappingInfo
                object. Defaults to True.
    :args:      Additional arguments to pass to the mapped function.
    :kwargs:    Additional keyword arguments to pass to the mapped function.
    :vim_exprs: Vim expressions to be evaluated and passed to the callback
                function, when the mapping is triggered.
    """
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    cb = MapCallback(
        func, info=(mode, keys), py_args=args, py_kwargs=kwargs or {},
        vim_exprs=vim_exprs, pass_info=pass_info)
    specials = [el for el in [
        '<buffer>' if buffer else '',
        '<silent>' if silent else '',
        '<unique>' if unique else '',
        '<nowait>' if nowait else ''] if el]
    if mode == 'normal':
        rhs = f':silent {cb.as_call()}<CR>'
    elif mode == 'insert':
        if command:
            rhs = rf'<C-\><C-N>:silent {cb.as_call()}<CR>'
        else:
            rhs = f'<C-R>={cb.as_invocation()}<CR>'
    elif mode == 'visual':
        rhs = f':<C-U>silent {cb.as_call()}<CR>'
    elif mode == 'op-pending':
        rhs = f':<C-U>silent {cb.as_call()}<CR>'
    else:
        raise NotImplementedError

    map_cmd = mode_to_map_command[mode]
    cmd = f'{map_cmd} <special> {" ".join(specials)} {keys} {rhs}'
    vim.command(cmd)


def nmap(
        keys: str, func: Callable,
        *, buffer: bool = True, silent: bool = True, unique: bool = False,
        pass_info=True, nowait: bool = False, args=(),
        kwargs: Optional[dict] = None):
    """Set up a normal mode  mapping that invokes a Python function.

    See `map` for argument details.
    """
    map(
        'normal', keys, func, buffer=buffer, silent=silent, unique=unique,
        nowait=nowait, args=args, kwargs=kwargs, pass_info=pass_info)


def xmap(
        keys: str, func: Callable,
        *, buffer: bool = True, silent: bool = True, unique: bool = False,
        pass_info=True, nowait: bool = False, args=(),
        kwargs: Optional[dict] = None):
    """Set up a visual mode mapping that invokes a Python function.

    See `map` for argument details.
    """
    map(
        'visual', keys, func, buffer=buffer, silent=silent, unique=unique,
        nowait=nowait, args=args, kwargs=kwargs, pass_info=pass_info)


def omap(
        keys: str, func: Callable,
        *, buffer: bool = True, silent: bool = True, unique: bool = False,
        pass_info=True, nowait: bool = False, args=(),
        kwargs: Optional[dict] = None):
    """Set up an operator-pending mode mapping that invokes a Python function.

    See `map` for argument details.
    """
    map(
        'op-pending', keys, func, buffer=buffer, silent=silent, unique=unique,
        nowait=nowait, args=args, kwargs=kwargs, pass_info=pass_info)


def imap(
        keys: str, func: Callable,
        *, buffer: bool = True, silent: bool = True, unique: bool = False,
        pass_info=True, nowait: bool = False, command: bool = False,
        args=(), kwargs: Optional[dict] = None):
    """Set up an insert mapping that invokes a Python function.

    See `map` for argument details.
    """
    map(
        'insert', keys, func, buffer=buffer, silent=silent, unique=unique,
        nowait=nowait, command=command, args=args, kwargs=kwargs,
        pass_info=pass_info)
