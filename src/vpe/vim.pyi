"""A type annotation stub file for Vim's built-in ``vim`` module.

This is only complete enough to support linting of VPE.

It is also a work-in-progress.
"""
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-builtin
# pylint: disable=unused-argument

class Buffer: ...

class Current: ...

class Dictionary(dict): ...

class Function:
    name: str = ''

class error(Exception): ...

class List(list): ...

class Range: ...

class TabPage: ...

class Window: ...

def command(expr: str) -> None: ...

def eval(expr: str) -> str | list | dict: ...

buffers: list[Buffer] = []
current: Current = Current()
tabpages: list[TabPage] = []
options: dict[str, int | str, list] = {}
vars: dict = {}
vvars: dict = {}
windows: list[Window] = []
