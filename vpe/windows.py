"""Enhanced buffer support.

This module provides the `Window` class. Normally you work with these classes
via the `Vim` class:<py>:

    lines = list(vim.current.window)
    buf = vim.windows[2]

You should not normally need to import this module directly.
"""

import collections.abc

import vim as _vim

import vpe
from vpe import proxies
from vpe import variables

__all__ = ('windows', 'Window')


class Window(proxies.Proxy):
    """Wrapper around a :vim:`python-window`.

    VPE creates and manages instances of this class as required. It is not
    intended that user code creates Window instances directly.
    """
    _writeable = set(('cursor', 'width', 'height'))

    @property
    def vars(self) -> variables.Variables:
        """The buffar vars wrapped as a `Variables` instance."""
        return variables.Variables(self._proxied.vars)

    def temp_options(self, **presets) -> proxies.TemporaryOptions:
        """Context used to temporarily change options.

        This does for a window what `Buffer.temp_options` does for buffer.
        """
        return proxies.TemporaryOptions(self.options, **presets)

    def goto(self) -> None:
        """Switch to this window, if possible."""
        vpe.vim_command(f'{self.number} wincmd w')


class Windows(proxies.CollectionProxy):
    """Wrapper around the built-in vim.windows.

    This is a proxy that extends the vim.Window behaviour in various ways.
    """
    def __init__(self, windows):
        super().__init__(windows)


windows = Windows(_vim.windows)
