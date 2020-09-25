"""Stub for the testing of the VPE module.

This takes the place of the real vim module in order to be able to unpickle
structures generated from within a Vim sessin.

It also provides enough stubbed iplementation such that operations on some
unpicked types will work as expected.
"""
from __future__ import annotations

from typing import Any, ClassVar, List, Dict, Generator, Tuple, Set, Optional
from typing import Callable, Union

import builtins
import re

__name__ = 'vim'  # pylint: disable=redefined-builtin
__qualname__ = 'vim'
__TEST__ = True


class error(Exception):
    """Stub type for documentation, type hinting and linting."""


class Base:
    """Base for all the other stub classes."""
    # pylint: disable=too-few-public-methods

    def __getattr__(self, name):
        # print("GET", self.__class__.__name__, name)
        raise AttributeError(
            f'{self.__class__.__name__} has no attribute {name!r}')


class Dictionary(Base):
    """Stub type for documentation, type hinting and linting."""
    settable: Set[str] = set(('errmsg',))

    def __init__(self, read_only=False):
        super().__init__()
        self.__dict__['_read_only'] = read_only

    def __getitem__(self, key: str) -> Any:
        if key == '__vpe_args_':
            return {}
        return ''

    def __setattr__(self, name: str, value: Any):
        if self._read_only:
            raise error(f'Cannot set variable v:{name!r}.')
        self.__dict__[name] = value

    def __setitem__(self, name: str, value: Any):
        if self._read_only:
            raise error(f'Cannot set variable v:{name!r}.')
        self.__dict__[name] = value

    def __iter__(self) -> Generator[str, None, None]:
        for name in self.__dict__:
            yield name

    def _set(self, name: str, value: Any):
        if name not in self.settable:
            raise error(f'Cannot set variable v:{name!r}.')
        self.__dict__[name] = value


class BufferList(Base):
    """Stub type for documentation, type hinting and linting."""
    buffers: ClassVar[Dict[int, Buffer]] = {}

    def __iter__(self) -> Generator[Buffer, None, None]:
        for b in self.buffers.values():
            yield b

    def __getitem__(self, key: str) -> Buffer:
        return Buffer('noname')


class Buffer(Base):
    """Stub type for documentation, type hinting and linting."""
    name: str = 'unnamed'
    _vars: dict = {}
    _valid: bool = True
    number: int = 1
    _options: dict = {}

    def __init__(self, name):
        super().__init__()
        self.name = name

    @property
    def vars(self):
        """The buffer variables."""
        return self._vars

    @property
    def valid(self):
        """The buffer valid flag."""
        return self._valid

    @property
    def options(self):
        """The buffer options."""
        return self._options


class WindowList(Base):
    """Stub type for documentation, type hinting and linting."""
    # pylint: disable=too-few-public-methods

    def __getitem__(self, key: int) -> Window:
        return Window(1)


class Window(Base):
    """Stub type for documentation, type hinting and linting."""
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(self, n):
        super().__init__()
        self.number = n
        self.buffer = None
        self.vars = {}
        self.options = {}
        self.row = 1
        self.col = 1
        self.valid = 1

    @property
    def tabpage(self) -> TabPage:
        """The current tab page."""
        return TabPage(1)


class TabPageList(Base):
    """Stub type for documentation, type hinting and linting."""
    # pylint: disable=too-few-public-methods

    def __getitem__(self, key: int) -> TabPage:
        return TabPage(key)

    def __len__(self):
        return 1


class TabPage(Base):
    """Stub type for documentation, type hinting and linting."""
    # pylint: disable=too-few-public-methods

    def __init__(self, n):
        super().__init__()
        self.windows: List[Window] = [Window(1)]
        self.vars: Dict[str, Any] = {}
        self.number: int = n
        self.valid: bool = True

    @property
    def window(self) -> Window:
        """The current window."""
        return Window(1)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)


class Current(Base):  # pylint: disable=too-few-public-methods
    """stub type for documentation, type hinting and linting."""

    def __init__(self):
        super().__init__()
        self.buffer = Buffer(1)


class Options(Base):
    """Stub type for documentation, type hinting and linting."""
    _unknown: Set[str] = set(('aardvark',))

    def __init__(self, read_only: Optional[List[str]] = None):
        super().__init__()
        self.__dict__['_read_only'] = read_only or []

    def __getitem__(self, name: str) -> Any:
        return self.__dict__.get(name, '')

    def __setitem__(self, name: str, value: Any):
        if name in self._read_only:
            raise error(f'Keyerror {name!r}')
        self.__dict__[name] = value

    def __contains__(self, name) -> bool:
        if name in self._unknown or name in self._read_only:
            return False
        if name not in self.__dict__:
            self.__dict__[name] = ''
        return name in self.__dict__

    def __iter__(self) -> Generator[str, None, None]:
        for name in self.__dict__:
            yield name

    def _set(self, name: str, value: Any):
        self.__dict__[name] = value

    def _knows(self, name: str) -> bool:
        if name in self._unknown:
            return False
        if name not in self.__dict__:
            self.__dict__[name] = ''
        return name in self.__dict__


class Function(Base):
    """Stub type for documentation, type hinting and linting."""
    # pylint: disable=too-few-public-methods
    def __init__(self, name: str, args=Optional[List[Any]]):
        self.name = name

    def __call__(self, *args):
        func = builtins.eval(self.name)
        return func(*args)


class Range(Base):
    """Stub type for documentation, type hinting and linting."""
    # pylint: disable=too-few-public-methods
    pass  # pylint: disable=unnecessary-pass


class Anything(Base):
    """A thing to represent any thing we do not care about."""
    # pylint: disable=too-few-public-methods

    def __call__(self, *args, **kwargs):
        return 0


e_varname = r'''
    (?P<amp> \&) ?
    (?P<vtype> [gvb] :) ?
    (?P<vname> [_a-zA-Z] [_a-zA-Z0-9]* )
'''

r_varname = re.compile(fr'''(?x)
    {e_varname} $
''')
r_assign = re.compile(fr'''(?x)
    let [ ] {e_varname}
    [ ]* = [ ]* (?P<expr> .* )
''')


def command(cmd: str) -> None:
    """Emulate vim command function."""
    m = r_assign.match(cmd.strip())
    if m:
        amp, vtype, vname, expr = m.groups()
        v = builtins.eval(expr)
        if amp == '&':
            options._set(vname, v)  # pylint: disable=protected-access
        elif vtype in ('g:', '', None):
            vars[vname] = v
        elif vtype == 'v:':
            vvars._set(vname, v)  # pylint: disable=protected-access
        else:
            # print("SKIP SET", m.groups())
            pass

    else:
        if command_callback:
            command_callback(cmd)


def normal(_cmd: str) -> None:
    """Emulate vom normal command."""


def eval(expr: str) -> Any:   # pylint: disable=redefined-builtin
    """Emulate vim eval method."""
    m = r_varname.match(expr.strip())
    if m:
        amp, vtype, vname = m.groups()
        if vtype in ('g:', ''):
            if amp:
                return options[vname]
            return vars[vname]
        if vtype == 'v:':
            return vvars[vname]
        # print(f'EVAL FAIL for buf var: {expr!r}')
        return ''

    try:
        return builtins.eval(expr)
    except Exception:  # pylint: disable=broad-except
        return ''


def exists(expr):
    """Test whether a Vim object, file, *etc.* exists."""
    if expr.startswith(':'):
        return '2'
    if expr.startswith('+'):
        # pylint: disable=protected-access
        return '1' if options._knows(expr[1:]) else '0'
    return '0'


def win_id2tabwin(_id: Any) -> Tuple[int, int]:
    """Get tab and window number for a given window ID."""
    return 1, 1


def win_getid(_win, _tab=None):
    """Get the ID of a window."""
    return 111


def register_command_callback(func: Union[Callable, None]):
    """Register a function to be invoked when vim.command is invoked.

    The callback function;s signature is:<py>:

        func(cmd: str): ...

    :func: The callback function.
    """
    global command_callback                 # pylint: disable=global-statement
    command_callback = func


vars = Dictionary()  # pylint: disable=redefined-builtin
vvars = Dictionary(read_only=True)
options = Options(read_only=['autoindent', 'fileformat'])
windows = WindowList()
buffers = BufferList()
tabpages = TabPageList()
current = Current()

# Aliases for some types.
dictionary = Dictionary
window = Window
list = List  # pylint: disable=redefined-builtin

command_callback: Optional[Callable] = None
