"""Special support for vim.Dictionary."""

import vim as _vim

from vpe import proxies

__all__ = ('Dictionary',)


class Dictionary(proxies.MutableMappingProxy):
    """Wrapper around vim.Dictionary and other mapping types.

    This makes the value appear more pythonic. For example ``for v in d`` works
    as might be expected.
    """
    def __init__(self, dict):
        super().__init__(dict)

    def __iter__(self):
        """Correctly support 'for v in dict'."""
        return iter(self._proxied.keys())
