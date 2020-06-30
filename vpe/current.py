"""Special support for current attribute."""

import vim as _vim

from vpe import proxies

__all__ = ('windows',)


class Current(proxies.Proxy):
    """Wrapper around the built-in vim.current attribute."""
    _writeable = set(('line', 'buffer', 'window', 'tabpage'))

    @property
    def _proxied(self):
        return _vim.current


current = Current()
