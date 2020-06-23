"""Special support for tab pages."""

import collections.abc

import vim as _vim

from vpe import proxies
from vpe import variables

__all__ = ('tabpages',)


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


tabpages = TabPages()
