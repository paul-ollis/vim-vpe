"""Enhanced module for using Python3 in Vim.

This provides the Vim class, which is a wrapper around Vim's built-in *vim*
module. It is intended that a Vim instance can be uses as a replacement for the
*vim* module. For example:

    import vpe
    vim = vpe.Vim()
    # Now use 'vim' as an extended version of the *vim* module.
    # ...

Note that ``vpe.Vim()`` always returns the same (singleton) instance.

This was developed for Vim version 8.1. It will probably work for Vim 8.0, but
is very unlikely to be compatible with earlier versions. I plan that future
versions of *vpe* will be backwardly compatible with version 8.1.
"""

import vim as _vim

from . import buffers
from . import commands
from . import dictionaries
from . import options
from . import tabpages
from . import windows

_wrappers = {
    type(_vim.buffers): buffers.Buffers,
    type(_vim.options): options.Options,
    type(_vim.tabpages): tabpages.TabPages,
    type(_vim.windows): windows.Windows,
    _vim.Buffer: buffers.Buffer,
    _vim.Dictionary:    dictionaries.Dictionary,
    _vim.Range: buffers.Range,
    _vim.TabPage: tabpages.TabPage,
    _vim.Window: windows.Window,
}
_blockedVimFunctions = set((
    "libcall",
    "libcallnr",
))
_vim_singletons = {
    'tabpages': tabpages.tabpages,
    'buffers': buffers.buffers,
    'windows': windows.windows,
    'options': options.global_options,
    'vars': variables.vars,
    'vvars': variables.vvars,
}


def wrap_item(item):
    wrapper = _wrappers.get(type(item), None)
    if wrapper is not None:
        return wrapper(item)
    return item


class Function(_vim.Function):
    """Wrapper around a vim.Function.

    This provides some minimal cooercion of function return types.
    """

    def __call__ (self, *args, **kwargs):
        v = super().__call__(*args, **kwargs)
        if isinstance(v, _vim.Dictionary):
            return dictionaries.Dictionary(v)
        return v


class _VimDirectFunctions:
    """Transparent access to Vim's functions."""

    def __getattr__(self, name):
        fname_form = f'*{name}'
        if _vim.eval(f'exists({fname_form!r})') != '0':
            if name not in _blockedVimFunctions:
                return Function(name)

        raise AttributeError(
            f'{self.__class__.__name__} object has no attribute {name!r}')


class _VimOverrides:
    """Overrides of the basic *vim* API."""

    def __getattr__(self, name):
        """For non-overridden attributes use the vim module's official API."""
        if name in _vim_singletons:
            return _vim_singletons[name]
        try:
            attr = getattr(_vim, name)
        except AttributeError:
            return super().__getattr__(name)
        else:
            return wrap_item(attr)

    def __setattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        else:
            raise AttributeError(
                f'can\'t set attribute {name} for {self.__class__.__name__}')


class Vim(
        _VimOverrides,
        _VimDirectFunctions,
    ):
    """A wrapper around and replacement for the *vim* module."""

    def __new__(cls, *args, **kwargs):
        """Ensure only a single Vim instance ever exists."""
        try:
            cls._myself
        except AttributeError:
            cls._myself = super().__new__(cls, *args, **kwargs)
        return cls._myself

    def vim(self):
        """Get the underlying built-in vim module."""
        return _vim


# Create a Vim instance for module use.
vim = Vim()
