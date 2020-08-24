"""Python support for key sequence mapping.

This module provides support for mapping key sequences to Python function
calls.
"""
from __future__ import annotations

from typing import Tuple, Optional, List, Callable
import traceback

import vim as _vim

from vpe import core
from vpe import vim
import vpe

mode_to_map_command = {
    'normal': 'nnoremap',
    'visual': 'xnoremap',
    'op-pending': 'onoremap',
    'insert': 'inoremap',
    # Not supported unless (and until) a valid use-case presents itself.
    # 'command':    cnoremap,
}

_VIM_FUNC_DEFS = """
function! VPE_MappingCall(uid)
    let g:vpe_args_ = {}
    let g:vpe_args_['uid'] = a:uid
    return py3eval('vpe.MapCallback.invoke()')
endfunction
"""
_vim.command(_VIM_FUNC_DEFS)


class MapCallback(core.Callback):
    """Wrapper for a function to be invoked by a key mapping."""
    caller = 'VPE_MappingCall'

    @classmethod
    def invoke(cls):
        try:
            uid = vim.vars.vpe_args_['uid']
            cb = cls.callbacks.get(uid, None)
            if cb is None:
                return 0
            ret = cb(vim_args=(), callargs=(MappingInfo(*cb.info),))
            if ret is None:
                ret = 0
            return ret

        except Exception as e:                   # pylint: disable=broad-except
            vpe.log(f'{e.__class__.__name__} {e}')
            traceback.print_exc(file=vpe.log)

        return -1


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
        nowait: bool = False, command: bool = False,
        args=(), kwargs: Optional[dict] = None):
    """Set up a key mapping that invokes a Python function.

    By default, the effective map command has the form:

       {m}noremap <buffer> <silent> keys ...

    Where {m} is one of n, x, o, i.

    The noremap form is always used.

    The first argument passed to the mapped function is a `MappingInfo` object.
    Additional arguments can be speficied using *args* and *kwargs*.

    For convenience, mode specific versions are provided (`nmap`, `xmap`,
    `omap` and `imap`). See those for details of what he mapped function can
    do. It is recommended that these mode specific versions are use in
    preference to this function.

    :mode:    A string defining the mode in which the mapping occurs. This
              should be one of: normal, visual, op-pending, insert, command.
    :keys:    The key sequence to be mapped.
    :func:    The Python function to invoke for the mapping.
    :buffer:  Use the <buffer> special argument. Defaults to True.
    :silent:  Use the <silent> special argument. Defaults to True.
    :unique:  Use the <unique> special argument. Defaults to False.
    :nowait:  Use the <nowait> special argument. Defaults to False.
    :command: Only applicable to insert mode. If true then the function
              is invoked from the command prompt and the return value is not
              used. Otherwise (the default) the function should return the
              text to be inserted.
    :args:    Additional arguments to pass to the mapped function.
    :kwargs:  Additional keyword arguments to pass to the mapped function.
    """
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    mapinfo = mode, keys
    kwargs = kwargs or {}
    cb = MapCallback(func, info=mapinfo, py_args=args, py_kwargs=kwargs)
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
        nowait: bool = False, args=(), kwargs: Optional[dict] = None):
    """Set up a normal mode  mapping that invokes a Python function.

    See `map` for argument details.
    """
    map(
        'normal', keys, func, buffer=buffer, silent=silent, unique=unique,
        nowait=nowait, args=args, kwargs=kwargs)


def xmap(
        keys: str, func: Callable,
        *, buffer: bool = True, silent: bool = True, unique: bool = False,
        nowait: bool = False, args=(), kwargs: Optional[dict] = None):
    """Set up a visual mode mapping that invokes a Python function.

    See `map` for argument details.
    """
    map(
        'visual', keys, func, buffer=buffer, silent=silent, unique=unique,
        nowait=nowait, args=args, kwargs=kwargs)


def omap(
        keys: str, func: Callable,
        *, buffer: bool = True, silent: bool = True, unique: bool = False,
        nowait: bool = False, args=(), kwargs: Optional[dict] = None):
    """Set up am operator-pending mode mapping that invokes a Python function.

    See `map` for argument details.
    """
    map(
        'op-pending', keys, func, buffer=buffer, silent=silent, unique=unique,
        nowait=nowait, args=args, kwargs=kwargs)


def imap(
        keys: str, func: Callable,
        *, buffer: bool = True, silent: bool = True, unique: bool = False,
        nowait: bool = False, command: bool = False,
        args=(), kwargs: Optional[dict] = None):
    """Set up an insert mapping that invokes a Python function.

    See `map` for argument details.
    """
    map(
        'insert', keys, func, buffer=buffer, silent=silent, unique=unique,
        nowait=nowait, command=command, args=args, kwargs=kwargs)
