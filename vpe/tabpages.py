"""Enhanced buffer support.

This module provides the `Window` class. Normally you work with these classes
via the `Vim` class:<py>:

    lines = list(vim.current.tabpage)
    tab = vim.tabpages[2]

You should not normally need to import this module directly.
"""

import collections.abc

import vim as _vim

import vpe
from vpe import commands
from vpe import proxies
from vpe import variables

__all__ = ('tabpages', 'TabPage')

_position_name_to_flag = {
    'after': '.',
    'before': '-',
    'first': '0',
    'last': '$'
}


class TabPage(proxies.Proxy):
    """Wrapper around a :vim:`python-tabpage`.

    VPE creates and manages instances of this class as required. It is not
    intended that user code creates TabPage instances directly.
    """
    _writeable = set()

    @property
    def vars(self):
        """The buffar vars wrapped as a `Variables` instance."""
        return variables.Variables(self._proxied)


class TabPages(proxies.CollectionProxy):
    """Wrapper around the built-in vim.tabpages.

    This is a proxy that extends the vim.TabPages behaviour in various ways.
    """
    @property
    def _proxied(self):
        return _vim.tabpages

    def new(self, *, position='after'):
        """Create a new tab page.

        :position:
            The position relative to this tab. The standard character prefixes
            for the ':tabnew' command can be used or one of the more readable
            strings:

            'after', 'before'
                Immediately after or before the current tab (same as '.', '-'),
            'first', 'last'
                As the first or last tab (same as '0', '$'),

            This defaults to 'after'.
        """
        flag = _position_name_to_flag.get(position, position)
        vpe.vim_command(f'{flag}tabnew')
        return vpe.vim.current.tabpage


tabpages = TabPages()
