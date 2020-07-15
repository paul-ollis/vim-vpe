"""Special support for tab pages."""

import collections.abc

import vim as _vim

import vpe
from vpe import commands
from vpe import proxies
from vpe import variables

__all__ = ('tabpages',)

_position_name_to_flag = {
    'after': '.',
    'before': '-',
    'first': '0',
    'last': '$'
}


# TODO: CollectionProxy is not the correct base class.
class TabPage(proxies.Proxy):
    """Wrapper around the built-in vim.TabPages type.

    This is a proxy that extends the vim.TabPages behaviour in various ways.
    """
    _writeable = set()

    @property
    def vars(self):
        """The buffar vars wrapped as a Variables instance."""
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

        :param position:
            The position relative to this tab. The standard character prefixes
            for the ':tabnew' command can be used or one of the more readable strings:

            'after', 'before'
                Immediately after or before the current tab (same as '.', '-'),
            'first', 'last'
                As the first or last tab (same as '0', '$'),

            This defaults to 'after'.
        """
        flag = _position_name_to_flag.get(position, position)
        _vim.command(f'{flag}tabnew')
        return vpe.vim.current.tabpage


tabpages = TabPages()
