"""Special support for windows."""

import collections.abc

import vim as _vim

from vpe import proxies
from vpe import variables

__all__ = ('windows',)


class Window(proxies.Proxy):
    """Wrapper around the built-in vim.Window type.

    This is a proxy that extends the vim.Window behaviour in various ways.
    """
    _writeable = set(('cursor', 'width', 'height'))

    @property
    def vars(self):
        """The buffar vars wrapped as a Variables instance."""
        return variables.Variables(self._proxied.vars)

    def temp_options(self, **presets):
        """Context used to temporarily change options."""
        return proxies.TemporaryOptions(self.options, **presets)

    def goto(self):
        """Switch to this window, if possible."""
        _vim.command(f'{self.number} wincmd w')


class Windows(proxies.CollectionProxy):
    """Wrapper around the built-in vim.windows.

    This is a proxy that extends the vim.Window behaviour in various ways.
    """
    def __init__(self, windows):
        super().__init__(windows)


windows = Windows(_vim.windows)
